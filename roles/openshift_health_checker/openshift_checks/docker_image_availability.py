"""Check that required Docker images are available."""

import re
from pipes import quote
from ansible.module_utils import six
from openshift_checks import OpenShiftCheck
from openshift_checks.mixins import DockerHostMixin


NODE_IMAGE_SUFFIXES = ["haproxy-router", "docker-registry", "deployer", "pod"]
DEPLOYMENT_IMAGE_INFO = {
    "origin": {
        "namespace": "openshift",
        "name": "origin",
        "registry_console_prefix": "docker.io/cockpit/",
        "registry_console_basename": "kubernetes",
        "registry_console_default_version": "latest",
    },
    "openshift-enterprise": {
        "namespace": "openshift3",
        "name": "ose",
        "registry_console_prefix": "registry.access.redhat.com/openshift3/",
        "registry_console_basename": "registry-console",
        "registry_console_default_version": "${short_version}",
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
    # command for checking if remote registries have an image, without docker pull
    skopeo_command = "{proxyvars} timeout 10 skopeo inspect --tls-verify={tls} {creds} docker://{registry}/{image}"
    skopeo_example_command = "skopeo inspect [--tls-verify=false] [--creds=<user>:<pass>] docker://<registry>/<image>"

    def __init__(self, *args, **kwargs):
        super(DockerImageAvailability, self).__init__(*args, **kwargs)

        self.registries = dict(
            # set of registries that need to be checked insecurely (note: not accounting for CIDR entries)
            insecure=set(self.ensure_list("openshift_docker_insecure_registries")),
            # set of registries that should never be queried even if given in the image
            blocked=set(self.ensure_list("openshift_docker_blocked_registries")),
        )

        # ordered list of registries (according to inventory vars) that docker will try for unscoped images
        regs = self.ensure_list("openshift_docker_additional_registries")
        # currently one of these registries is added whether the user wants it or not.
        deployment_type = self.get_var("openshift_deployment_type", default="")
        if deployment_type == "origin" and "docker.io" not in regs:
            regs.append("docker.io")
        elif deployment_type == 'openshift-enterprise' and "registry.access.redhat.com" not in regs:
            regs.append("registry.access.redhat.com")
        self.registries["configured"] = regs

        # for the oreg_url registry there may be credentials specified
        oreg_url = self.get_var("oreg_url", default="")
        oreg_url = self.template_var(oreg_url)
        components = oreg_url.split('/')
        self.registries["oreg"] = "" if len(components) < 3 else components[0]

        # Retrieve and template registry credentials, if provided
        self.skopeo_command_creds = ""
        oreg_auth_user = self.get_var('oreg_auth_user', default='')
        oreg_auth_password = self.get_var('oreg_auth_password', default='')
        if oreg_auth_user != '' and oreg_auth_password != '':
            oreg_auth_user = self.template_var(oreg_auth_user)
            oreg_auth_password = self.template_var(oreg_auth_password)
            self.skopeo_command_creds = quote("--creds={}:{}".format(oreg_auth_user, oreg_auth_password))

        # record whether we could reach a registry or not (and remember results)
        self.reachable_registries = {}

        # take note of any proxy settings needed
        proxies = []
        for var in ['http_proxy', 'https_proxy', 'no_proxy']:
            # ansible vars are openshift_http_proxy, openshift_https_proxy, openshift_no_proxy
            value = self.get_var("openshift_" + var, default=None)
            if value:
                proxies.append(var.upper() + "=" + quote(self.template_var(value)))
        self.skopeo_proxy_vars = " ".join(proxies)

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

        available_images = self.available_images(missing_images)
        unavailable_images = set(missing_images) - set(available_images)

        if unavailable_images:
            unreachable = [reg for reg, reachable in self.reachable_registries.items() if not reachable]
            unreachable_msg = u"Failed connecting to: {}\n".format(u", ".join(unreachable))
            blocked_msg = u"Blocked registries: {}\n".format(u", ".join(self.registries["blocked"]))
            missing = u",\n    ".join(sorted(unavailable_images))

            msg = (
                u"One or more required container images are not available:\n    {missing}\n"
                "Checked with: {cmd}\n"
                "Default registries searched: {registries}\n"
                "{blocked}"
                "{unreachable}"
            ).format(
                missing=missing,
                cmd=self.skopeo_example_command,
                registries=", ".join(self.registries["configured"]),
                blocked=blocked_msg if self.registries["blocked"] else "",
                unreachable=unreachable_msg if unreachable else "",
            )

            return dict(failed=True, msg=msg.encode('utf8') if six.PY2 else msg)

        return {}

    def required_images(self):
        """
        Determine which images we expect to need for this host.
        Returns: a set of required images like 'docker.io/openshift/origin:v3.6'

        The thorny issue of determining the image names from the variables is under consideration
        via https://github.com/openshift/openshift-ansible/issues/4415

        For now we operate as follows:
        * For containerized components (master, node, ...) we look at the deployment
          type and use docker.io/openshift/origin or
          registry.access.redhat.com/openshift3/ose as the base for those component
          images. The version is openshift_image_tag as determined by the
          openshift_version role.
        * For OpenShift-managed infrastructure (router, registry...) we use oreg_url if
          it is defined; otherwise we again use the base that depends on the deployment type.
        Registry is not included in constructed images. It may be in oreg_url or etcd image.
        """
        required = set()
        deployment_type = self.get_var("openshift_deployment_type")
        host_groups = self.get_var("group_names")
        # containerized etcd may not have openshift_image_tag, see bz 1466622
        image_tag = self.get_var("openshift_image_tag", default="latest")
        image_tag = self.template_var(image_tag)
        image_info = DEPLOYMENT_IMAGE_INFO[deployment_type]

        # template for images that run on top of OpenShift
        image_url = "{}/{}-{}:{}".format(image_info["namespace"], image_info["name"], "${component}", "${version}")
        image_url = self.get_var("oreg_url", default="") or image_url
        image_url = self.template_var(image_url)
        if 'oo_nodes_to_config' in host_groups:
            for suffix in NODE_IMAGE_SUFFIXES:
                required.add(image_url.replace("${component}", suffix).replace("${version}", image_tag))
            if self.get_var("osm_use_cockpit", default=True, convert=bool):
                required.add(self._registry_console_image(image_tag, image_info))

        if self.get_var("openshift_is_atomic", convert=bool):
            if 'oo_nodes_to_config' in host_groups:
                required.add(self.template_var(self.get_var('osn_image', default='')))

        return required

    def _registry_console_image(self, image_tag, image_info):
        """Returns image with logic to parallel what happens with the registry-console template."""
        # The registry-console is for some reason not prefixed with ose- like the other components.
        # Nor is it versioned the same. Also a completely different name is used for Origin.
        prefix = self.get_var(
            "openshift_cockpit_deployer_prefix",
            default=image_info["registry_console_prefix"],
        )
        basename = self.get_var(
            "openshift_cockpit_deployer_basename",
            default=image_info["registry_console_basename"],
        )

        # enterprise template just uses v3.6, v3.7, etc
        match = re.match(r'v\d+\.\d+', image_tag)
        short_version = match.group() if match else image_tag
        version = image_info["registry_console_default_version"].replace("${short_version}", short_version)
        version = self.get_var("openshift_cockpit_deployer_version", default=version)

        return prefix + basename + ':' + version

    def local_images(self, images):
        """Filter a list of images and return those available locally."""
        found_images = []
        for image in images:
            # docker could have the image name as-is or prefixed with any registry
            imglist = [image] + [reg + "/" + image for reg in self.registries["configured"]]
            if self.is_image_local(imglist):
                found_images.append(image)
        return found_images

    def is_image_local(self, image):
        """Check if image is already in local docker index."""
        result = self.execute_module("docker_image_facts", {"name": image})
        return bool(result.get("images")) and not result.get("failed")

    def ensure_list(self, registry_param):
        """Return the task var as a list."""
        # https://bugzilla.redhat.com/show_bug.cgi?id=1497274
        # If the result was a string type, place it into a list. We must do this
        # as using list() on a string will split the string into its characters.
        # Otherwise cast to a list as was done previously.
        registry = self.get_var(registry_param, default=[])
        if not isinstance(registry, six.string_types):
            return list(registry)
        return self.normalize(registry)

    def available_images(self, images):
        """Search remotely for images. Returns: list of images found."""
        return [
            image for image in images
            if self.is_available_skopeo_image(image)
        ]

    def is_available_skopeo_image(self, image):
        """Use Skopeo to determine if required image exists in known registry(s)."""
        registries = self.registries["configured"]
        # If image already includes a registry, only use that.
        # NOTE: This logic would incorrectly identify images that do not use a namespace, e.g.
        # registry.access.redhat.com/rhel7 as if the registry were a namespace.
        # It's not clear that there's any way to distinguish them, but fortunately
        # the current set of images all look like [registry/]namespace/name[:version].
        if image.count("/") > 1:
            registry, image = image.split("/", 1)
            registries = [registry]

        for registry in registries:
            if registry in self.registries["blocked"]:
                continue  # blocked will never be consulted
            if registry not in self.reachable_registries:
                self.reachable_registries[registry] = self.connect_to_registry(registry)
            if not self.reachable_registries[registry]:
                continue  # do not keep trying unreachable registries

            if six.PY2:
                registry = registry.encode('utf8')
                image = image.encode('utf8')

            args = dict(
                proxyvars=self.skopeo_proxy_vars,
                tls="false" if registry in self.registries["insecure"] else "true",
                creds=self.skopeo_command_creds if registry == self.registries["oreg"] else "",
                registry=quote(registry),
                image=quote(image),
            )

            result = self.execute_module_with_retries("command", {
                "_uses_shell": True,
                "_raw_params": self.skopeo_command.format(**args),
            })
            if result.get("rc", 0) == 0 and not result.get("failed"):
                return True
            if result.get("rc") == 124:  # RC 124 == timed out; mark unreachable
                self.reachable_registries[registry] = False

        return False

    def connect_to_registry(self, registry):
        """Use ansible wait_for module to test connectivity from host to registry. Returns bool."""
        if self.skopeo_proxy_vars != "":
            # assume we can't connect directly; just waive the test
            return True

        # test a simple TCP connection
        host, _, port = registry.partition(":")
        port = port or 443
        args = dict(host=host, port=port, state="started", timeout=30)
        result = self.execute_module("wait_for", args)
        return result.get("rc", 0) == 0 and not result.get("failed")
