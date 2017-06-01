# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, get_var
from openshift_checks.mixins import DockerHostMixin


class DockerImageAvailability(DockerHostMixin, OpenShiftCheck):
    """Check that required Docker images are available.

    This check attempts to ensure that required docker images are
    either present locally, or able to be pulled down from available
    registries defined in a host machine.
    """

    name = "docker_image_availability"
    tags = ["preflight"]

    dependencies = ["skopeo", "python-docker-py"]

    deployment_image_info = {
        "origin": {
            "namespace": "openshift",
            "name": "origin",
        },
        "openshift-enterprise": {
            "namespace": "openshift3",
            "name": "ose",
        },
    }

    @classmethod
    def is_active(cls, task_vars):
        """Skip hosts with unsupported deployment types."""
        deployment_type = get_var(task_vars, "openshift_deployment_type")
        has_valid_deployment_type = deployment_type in cls.deployment_image_info

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

    def required_images(self, task_vars):
        deployment_type = get_var(task_vars, "openshift_deployment_type")
        image_info = self.deployment_image_info[deployment_type]

        openshift_release = get_var(task_vars, "openshift_release", default="latest")
        openshift_image_tag = get_var(task_vars, "openshift_image_tag")
        is_containerized = get_var(task_vars, "openshift", "common", "is_containerized")

        images = set(self.required_docker_images(
            image_info["namespace"],
            image_info["name"],
            ["registry-console"] if "enterprise" in deployment_type else [],  # include enterprise-only image names
            openshift_release,
            is_containerized,
        ))

        # append images with qualified image tags to our list of required images.
        # these are images with a (v0.0.0.0) tag, rather than a standard release
        # format tag (v0.0). We want to check this set in both containerized and
        # non-containerized installations.
        images.update(
            self.required_qualified_docker_images(
                image_info["namespace"],
                image_info["name"],
                openshift_image_tag,
            ),
        )

        return images

    @staticmethod
    def required_docker_images(namespace, name, additional_image_names, version, is_containerized):
        if is_containerized:
            return ["{}/{}:{}".format(namespace, name, version)] if name else []

        # include additional non-containerized images specific to the current deployment type
        return ["{}/{}:{}".format(namespace, img_name, version) for img_name in additional_image_names]

    @staticmethod
    def required_qualified_docker_images(namespace, name, version):
        # pylint: disable=invalid-name
        return [
            "{}/{}-{}:{}".format(namespace, name, suffix, version)
            for suffix in ["haproxy-router", "docker-registry", "deployer", "pod"]
        ]

    def local_images(self, images, task_vars):
        """Filter a list of images and return those available locally."""
        return [
            image for image in images
            if self.is_image_local(image, task_vars)
        ]

    def is_image_local(self, image, task_vars):
        result = self.module_executor("docker_image_facts", {"name": image}, task_vars)
        if result.get("failed", False):
            return False

        return bool(result.get("images", []))

    @staticmethod
    def known_docker_registries(task_vars):
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
            if any(self.is_available_skopeo_image(image, registry, task_vars) for registry in registries)
        ]

    def is_available_skopeo_image(self, image, registry, task_vars):
        """Uses Skopeo to determine if required image exists in a given registry."""

        cmd_str = "skopeo inspect docker://{registry}/{image}".format(
            registry=registry,
            image=image,
        )

        args = {"_raw_params": cmd_str}
        result = self.module_executor("command", args, task_vars)
        return not result.get("failed", False) and result.get("rc", 0) == 0
