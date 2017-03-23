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

    docker_image_base = {
        "origin": {
            "repo": "openshift",
            "image": "origin",
        },
        "openshift-enterprise": {
            "repo": "openshift3",
            "image": "ose",
        },
    }

    def run(self, tmp, task_vars):
        required_images = self.required_images(task_vars)
        missing_images = set(required_images) - set(self.local_images(required_images, task_vars))

        # exit early if all images were found locally
        if not missing_images:
            return {"changed": False}

        msg, failed, changed = self.update_skopeo_image(task_vars)

        # exit early if Skopeo update fails
        if failed:
            return {
                "failed": True,
                "changed": changed,
                "msg": "Failed to update Skopeo image ({img_name}). {msg}".format(img_name=self.skopeo_image, msg=msg),
            }

        registries = self.known_docker_registries(task_vars)
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
        deployment_type = get_var(task_vars, "deployment_type")
        image_base_name = self.docker_image_base[deployment_type]

        openshift_release = get_var(task_vars, "openshift_release")
        openshift_image_tag = get_var(task_vars, "openshift_image_tag")

        is_containerized = get_var(task_vars, "openshift", "common", "is_containerized")

        if is_containerized:
            images = set(self.containerized_docker_images(image_base_name, openshift_release))
        else:
            images = set(self.rpm_docker_images(image_base_name, openshift_release))

        # append images with qualified image tags to our list of required images.
        # these are images with a (v0.0.0.0) tag, rather than a standard release
        # format tag (v0.0). We want to check this set in both containerized and
        # non-containerized installations.
        images.update(
            self.qualified_docker_images(self.image_from_base_name(image_base_name), "v" + openshift_image_tag)
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
            return []

        docker_info = result.get("info", "")
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
        return result.get("failed", False)

    def containerized_docker_images(self, base_name, version):
        return [
            "{image}:{version}".format(image=self.image_from_base_name(base_name), version=version)
        ]

    @staticmethod
    def rpm_docker_images(base, version):
        return [
            "{image_repo}/registry-console:{version}".format(image_repo=base["repo"], version=version)
        ]

    @staticmethod
    def qualified_docker_images(image_name, version):
        return [
            "{}-{}:{}".format(image_name, component, version)
            for component in "haproxy-router docker-registry deployer pod".split()
        ]

    @staticmethod
    def image_from_base_name(base):
        return "".join([base["repo"], "/", base["image"]])

    # ensures that the skopeo docker image exists, and updates it
    # with latest if image was already present locally.
    def update_skopeo_image(self, task_vars):
        result = self.module_executor("docker_image", {"name": self.skopeo_image}, task_vars)
        return result.get("msg", ""), result.get("failed", False), result.get("changed", False)
