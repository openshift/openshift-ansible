# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, get_var


class DockerImageAvailability(OpenShiftCheck):
    """Check that required Docker images are available.

    This check attempts to ensure that required docker images are
    either present locally, or able to be pulled down from available
    registries defined in a host machine.
    """

    name = "docker_image_availability"
    tags = ["preflight"]

    skopeo_image = "openshift/openshift-ansible"

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
        required_images = self.required_images(task_vars)
        missing_images = set(required_images) - set(self.local_images(required_images, task_vars))

        # exit early if all images were found locally
        if not missing_images:
            return {"changed": False}

        msg, failed, changed = self.update_skopeo_image(task_vars)

        # exit early if Skopeo update fails
        if failed:
            if "Error connecting: Error while fetching server API version" in msg:
                msg = (
                    "It appears Docker is not running.\n"
                    "Please start Docker on this host before running this check.\n"
                    "The full error reported was:\n  " + msg
                    )

            elif "Failed to import docker-py" in msg:
                msg = (
                    "The required Python docker-py module is not installed.\n"
                    "Suggestion: install the python-docker-py package on this host."
                    )
            else:
                msg = "The full message reported by the docker_image module was:\n" + msg
            return {
                "failed": True,
                "changed": changed,
                "msg": (
                    "Unable to update the {img_name} image on this host;\n"
                    "This is required in order to check Docker image availability.\n"
                    "{msg}"
                    ).format(img_name=self.skopeo_image, msg=msg),
            }

        registries = self.known_docker_registries(task_vars)
        if not registries:
            return {"failed": True, "msg": "Unable to retrieve any docker registries."}

        available_images = self.available_images(missing_images, registries, task_vars)
        unavailable_images = set(missing_images) - set(available_images)

        if unavailable_images:
            return {
                "failed": True,
                "msg": (
                    "One or more required images are not available: {}.\n"
                    "Configured registries: {}"
                ).format(", ".join(sorted(unavailable_images)), ", ".join(registries)),
                "changed": changed,
            }

        return {"changed": changed}

    def required_images(self, task_vars):
        deployment_type = get_var(task_vars, "openshift_deployment_type")
        image_info = self.deployment_image_info[deployment_type]

        openshift_release = get_var(task_vars, "openshift_release", default="latest")
        openshift_image_tag = get_var(task_vars, "openshift_image_tag", default=openshift_release)
        if openshift_image_tag and openshift_image_tag[0] != 'v':
            openshift_image_tag = 'v' + openshift_image_tag

        is_containerized = get_var(task_vars, "openshift", "common", "is_containerized")
        images = set(self.non_qualified_docker_images(image_info["namespace"], image_info["name"], openshift_release,
                                                      is_containerized))

        # append images with qualified image tags to our list of required images.
        # these are images with a (v0.0.0.0) tag, rather than a standard release
        # format tag (v0.0). We want to check this set in both containerized and
        # non-containerized installations.
        images.update(
            self.qualified_docker_images(image_info["namespace"], image_info["name"], openshift_image_tag)
        )

        return images

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

    def known_docker_registries(self, task_vars):
        result = self.module_executor("docker_info", {}, task_vars)
        if result.get("failed", False):
            return False

        docker_info = result.get("info", {})
        return [registry.get("Name", "") for registry in docker_info.get("Registries", {})]

    def available_images(self, images, registries, task_vars):
        """Inspect existing images using Skopeo and return all images successfully inspected."""
        return [
            image for image in images
            if self.is_image_available(image, registries, task_vars)
        ]

    def is_image_available(self, image, registries, task_vars):
        for registry in registries:
            if self.is_available_skopeo_image(image, registry, task_vars):
                return True

        return False

    def is_available_skopeo_image(self, image, registry, task_vars):
        """Uses Skopeo to determine if required image exists in a given registry."""

        cmd_str = "skopeo inspect docker://{registry}/{image}".format(
            registry=registry,
            image=image,
        )

        args = {
            "name": "skopeo_inspect",
            "image": self.skopeo_image,
            "command": cmd_str,
            "detach": False,
            "cleanup": True,
        }
        result = self.module_executor("docker_container", args, task_vars)
        return not result.get("failed", False)

    @staticmethod
    def non_qualified_docker_images(namespace, name, version, is_containerized):
        if is_containerized:
            return ["{}/{}:{}".format(namespace, name, version)] if name else []

        return ["{}/{}:{}".format(namespace, name, version)] if name else []

    @staticmethod
    def qualified_docker_images(namespace, name, version):
        return [
            "{}/{}-{}:{}".format(namespace, name, suffix, version)
            for suffix in ["haproxy-router", "docker-registry", "deployer", "pod"]
        ]

    # ensures that the skopeo docker image exists, and updates it
    # with latest if image was already present locally.
    def update_skopeo_image(self, task_vars):
        result = self.module_executor("docker_image", {"name": self.skopeo_image}, task_vars)
        return result.get("msg", ""), result.get("failed", False), result.get("changed", False)
