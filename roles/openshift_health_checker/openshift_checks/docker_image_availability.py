"""Check that required Docker images are available."""

from openshift_checks import OpenShiftCheck
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

    Determine docker images that an install would require and check that they
    are either present in the host's docker index, or available for the host to pull
    with known registries as defined in our inventory file (or defaults).
    """

    name = "docker_image_availability"
    tags = ["preflight"]
    # we use python-docker-py to check local docker for images, and skopeo
    # to look for images available remotely without waiting to pull them.
    dependencies = ["python-docker-py", "skopeo"]

    def is_active(self):
        """Skip hosts with unsupported deployment types."""
        deployment_type = self.get_var("openshift_deployment_type")
        has_valid_deployment_type = deployment_type in DEPLOYMENT_IMAGE_INFO

        return super(DockerImageAvailability, self).is_active() and has_valid_deployment_type

    def run(self):
        msg, failed = self.ensure_dependencies()
        if failed:
            return {
                "failed": True,
                "msg": "Some dependencies are required in order to check Docker image availability.\n" + msg
            }

        required_images = self.required_images()
        missing_images = set(required_images) - set(self.local_images(required_images))

        # exit early if all images were found locally
        if not missing_images:
            return {}

        registries = self.known_docker_registries()
        if not registries:
            return {"failed": True, "msg": "Unable to retrieve any docker registries."}

        available_images = self.available_images(missing_images, registries)
        unavailable_images = set(missing_images) - set(available_images)

        if unavailable_images:
            return {
                "failed": True,
                "msg": (
                    "One or more required Docker images are not available:\n    {}\n"
                    "Configured registries: {}"
                ).format(",\n    ".join(sorted(unavailable_images)), ", ".join(registries)),
            }

        return {}

    def required_images(self):
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
        deployment_type = self.get_var("openshift_deployment_type")
        host_groups = self.get_var("group_names")
        # containerized etcd may not have openshift_image_tag, see bz 1466622
        image_tag = self.get_var("openshift_image_tag", default="latest")
        image_info = DEPLOYMENT_IMAGE_INFO[deployment_type]
        if not image_info:
            return required

        # template for images that run on top of OpenShift
        image_url = "{}/{}-{}:{}".format(image_info["namespace"], image_info["name"], "${component}", "${version}")
        image_url = self.get_var("oreg_url", default="") or image_url
        if 'nodes' in host_groups:
            for suffix in NODE_IMAGE_SUFFIXES:
                required.add(image_url.replace("${component}", suffix).replace("${version}", image_tag))
            # The registry-console is for some reason not prefixed with ose- like the other components.
            # Nor is it versioned the same, so just look for latest.
            # Also a completely different name is used for Origin.
            required.add(image_info["registry_console_image"])

        # images for containerized components
        if self.get_var("openshift", "common", "is_containerized"):
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

    def local_images(self, images):
        """Filter a list of images and return those available locally."""
        return [
            image for image in images
            if self.is_image_local(image)
        ]

    def is_image_local(self, image):
        """Check if image is already in local docker index."""
        result = self.execute_module("docker_image_facts", {"name": image})
        if result.get("failed", False):
            return False

        return bool(result.get("images", []))

    def known_docker_registries(self):
        """Build a list of docker registries available according to inventory vars."""
        docker_facts = self.get_var("openshift", "docker")
        regs = set(docker_facts["additional_registries"])

        deployment_type = self.get_var("openshift_deployment_type")
        if deployment_type == "origin":
            regs.update(["docker.io"])
        elif "enterprise" in deployment_type:
            regs.update(["registry.access.redhat.com"])

        return list(regs)

    def available_images(self, images, default_registries):
        """Search remotely for images. Returns: list of images found."""
        return [
            image for image in images
            if self.is_available_skopeo_image(image, default_registries)
        ]

    def is_available_skopeo_image(self, image, default_registries):
        """Use Skopeo to determine if required image exists in known registry(s)."""
        registries = default_registries

        # if image already includes a registry, only use that
        if image.count("/") > 1:
            registry, image = image.split("/", 1)
            registries = [registry]

        for registry in registries:
            args = {
                "_raw_params": "timeout 10 skopeo inspect --tls-verify=false "
                               "docker://{}/{}".format(registry, image)
            }
            result = self.execute_module("command", args)
            if result.get("rc", 0) == 0 and not result.get("failed"):
                return True

        return False
