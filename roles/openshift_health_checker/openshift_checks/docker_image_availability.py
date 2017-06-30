"""Check that required Docker images are available."""

from openshift_checks import OpenShiftCheck, get_var
from openshift_checks.mixins import DockerHostMixin


NODE_IMAGE_SUFFIXES = ["haproxy-router", "docker-registry", "deployer", "pod"]
DEPLOYMENT_IMAGE_INFO = {
    "origin": {
        "namespace": "openshift",
        "name": "origin",
        "registry_console_image": "cockpit/kubernetes",
    },
    "openshift-enterprise": {
        "namespace": "openshift3",
        "name": "ose",
        "registry_console_image": "registry.access.redhat.com/openshift3/registry-console",
    },
}


class DockerImageAvailability(DockerHostMixin, OpenShiftCheck):
    """Check that required Docker images are available.

    This check attempts to ensure that required docker images are
    either present locally, or able to be pulled down from available
    registries defined in a host machine.
    """

    name = "docker_image_availability"
    tags = ["preflight"]
    dependencies = ["skopeo", "python-docker-py"]

    @classmethod
    def is_active(cls, task_vars):
        """Skip hosts with unsupported deployment types."""
        deployment_type = get_var(task_vars, "openshift_deployment_type")
        has_valid_deployment_type = deployment_type in DEPLOYMENT_IMAGE_INFO

        return super(DockerImageAvailability, cls).is_active(task_vars) and has_valid_deployment_type

    def run(self, tmp, task_vars):
        msg, failed, changed = self.ensure_dependencies(task_vars)
        if failed:
            return {
                "failed": True,
                "changed": changed,
                "msg": "Some dependencies are required in order to check Docker image availability.\n" + msg
            }

        required_images = self.required_images(task_vars)
        missing_images = set(required_images) - set(self.local_images(required_images, task_vars))

        # exit early if all images were found locally
        if not missing_images:
            return {"changed": changed}

        registries = self.known_docker_registries(task_vars)
        if not registries:
            return {"failed": True, "msg": "Unable to retrieve any docker registries.", "changed": changed}

        available_images = self.available_images(missing_images, registries, task_vars)
        unavailable_images = set(missing_images) - set(available_images)

        if unavailable_images:
            return {
                "failed": True,
                "msg": (
                    "One or more required Docker images are not available:\n    {}\n"
                    "Configured registries: {}"
                ).format(",\n    ".join(sorted(unavailable_images)), ", ".join(registries)),
                "changed": changed,
            }

        return {"changed": changed}

    @staticmethod
    def required_images(task_vars):
        """
        Determine which images we expect to need for this host.
        Returns: a set of required images like 'openshift/origin:v3.6'

        The thorny issue of determining the image names from the variables is under consideration
        via https://github.com/openshift/openshift-ansible/issues/4415

        For now we operate as follows:
        * For containerized components (master, node, ...) we look at the deployment type and
          use openshift/origin or openshift3/ose as the base for those component images. The
          version is openshift_image_tag as determined by the openshift_version role.
        * For OpenShift-managed infrastructure (router, registry...) we use oreg_url if
          it is defined; otherwise we again use the base that depends on the deployment type.
        Registry is not included in constructed images. It may be in oreg_url or etcd image.
        """
        required = set()
        deployment_type = get_var(task_vars, "openshift_deployment_type")
        host_groups = get_var(task_vars, "group_names")
        # containerized etcd may not have openshift_image_tag, see bz 1466622
        image_tag = get_var(task_vars, "openshift_image_tag", default="latest")
        image_info = DEPLOYMENT_IMAGE_INFO[deployment_type]
        if not image_info:
            return required

        # template for images that run on top of OpenShift
        image_url = "{}/{}-{}:{}".format(image_info["namespace"], image_info["name"], "${component}", "${version}")
        image_url = get_var(task_vars, "oreg_url", default="") or image_url
        if 'nodes' in host_groups:
            for suffix in NODE_IMAGE_SUFFIXES:
                required.add(image_url.replace("${component}", suffix).replace("${version}", image_tag))
            # The registry-console is for some reason not prefixed with ose- like the other components.
            # Nor is it versioned the same, so just look for latest.
            # Also a completely different name is used for Origin.
            required.add(image_info["registry_console_image"])

        # images for containerized components
        if get_var(task_vars, "openshift", "common", "is_containerized"):
            components = set()
            if 'nodes' in host_groups:
                components.update(["node", "openvswitch"])
            if 'masters' in host_groups:  # name is "origin" or "ose"
                components.add(image_info["name"])
            for component in components:
                required.add("{}/{}:{}".format(image_info["namespace"], component, image_tag))
            if 'etcd' in host_groups:  # special case, note it is the same for origin/enterprise
                required.add("registry.access.redhat.com/rhel7/etcd")  # and no image tag

        return required

    def local_images(self, images, task_vars):
        """Filter a list of images and return those available locally."""
        return [
            image for image in images
            if self.is_image_local(image, task_vars)
        ]

    def is_image_local(self, image, task_vars):
        """Check if image is already in local docker index."""
        result = self.execute_module("docker_image_facts", {"name": image}, task_vars=task_vars)
        if result.get("failed", False):
            return False

        return bool(result.get("images", []))

    @staticmethod
    def known_docker_registries(task_vars):
        """Build a list of docker registries available according to inventory vars."""
        docker_facts = get_var(task_vars, "openshift", "docker")
        regs = set(docker_facts["additional_registries"])

        deployment_type = get_var(task_vars, "openshift_deployment_type")
        if deployment_type == "origin":
            regs.update(["docker.io"])
        elif "enterprise" in deployment_type:
            regs.update(["registry.access.redhat.com"])

        return list(regs)

    def available_images(self, images, registries, task_vars):
        """Inspect existing images using Skopeo and return all images successfully inspected."""
        return [
            image for image in images
            if self.is_available_skopeo_image(image, registries, task_vars)
        ]

    def is_available_skopeo_image(self, image, registries, task_vars):
        """Use Skopeo to determine if required image exists in known registry(s)."""

        # if image does already includes a registry, just use that
        if image.count("/") > 1:
            registry, image = image.split("/", 1)
            registries = [registry]

        for registry in registries:
            args = {"_raw_params": "skopeo inspect --tls-verify=false docker://{}/{}".format(registry, image)}
            result = self.execute_module("command", args, task_vars=task_vars)
            if result.get("rc", 0) == 0 and not result.get("failed"):
                return True

        return False
