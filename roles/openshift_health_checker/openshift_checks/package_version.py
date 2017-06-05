# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, OpenShiftCheckException, get_var
from openshift_checks.mixins import NotContainerizedMixin


class PackageVersion(NotContainerizedMixin, OpenShiftCheck):
    """Check that available RPM packages match the required versions."""

    name = "package_version"
    tags = ["preflight"]

    openshift_to_ovs_version = {
        "3.6": "2.6",
        "3.5": "2.6",
        "3.4": "2.4",
    }

    openshift_to_docker_version = {
        "3.1": "1.8",
        "3.2": "1.10",
        "3.3": "1.10",
        "3.4": "1.12",
    }

    # map major release versions across releases
    # to a common major version
    openshift_major_release_version = {
        "1": "3",
    }

    @classmethod
    def is_active(cls, task_vars):
        """Skip hosts that do not have package requirements."""
        group_names = get_var(task_vars, "group_names", default=[])
        master_or_node = 'masters' in group_names or 'nodes' in group_names
        return super(PackageVersion, cls).is_active(task_vars) and master_or_node

    def run(self, tmp, task_vars):
        rpm_prefix = get_var(task_vars, "openshift", "common", "service_type")
        openshift_release = get_var(task_vars, "openshift_release", default='')
        deployment_type = get_var(task_vars, "openshift_deployment_type")
        check_multi_minor_release = deployment_type in ['openshift-enterprise']

        args = {
            "package_list": [
                {
                    "name": "openvswitch",
                    "version": self.get_required_ovs_version(task_vars),
                    "check_multi": False,
                },
                {
                    "name": "docker",
                    "version": self.get_required_docker_version(task_vars),
                    "check_multi": False,
                },
                {
                    "name": "{}".format(rpm_prefix),
                    "version": openshift_release,
                    "check_multi": check_multi_minor_release,
                },
                {
                    "name": "{}-master".format(rpm_prefix),
                    "version": openshift_release,
                    "check_multi": check_multi_minor_release,
                },
                {
                    "name": "{}-node".format(rpm_prefix),
                    "version": openshift_release,
                    "check_multi": check_multi_minor_release,
                },
            ],
        }

        return self.execute_module("aos_version", args, tmp, task_vars)

    def get_required_ovs_version(self, task_vars):
        """Return the correct Open vSwitch version for the current OpenShift version.
        If the current OpenShift version is >= 3.5, ensure Open vSwitch version 2.6,
        Else ensure Open vSwitch version 2.4"""
        openshift_version = self.get_openshift_version(task_vars)

        if float(openshift_version) < 3.5:
            return self.openshift_to_ovs_version["3.4"]

        ovs_version = self.openshift_to_ovs_version.get(str(openshift_version))
        if ovs_version:
            return ovs_version

        msg = "There is no recommended version of Open vSwitch for the current version of OpenShift: {}"
        raise OpenShiftCheckException(msg.format(openshift_version))

    def get_required_docker_version(self, task_vars):
        """Return the correct Docker version for the current OpenShift version.
        If the OpenShift version is 3.1, ensure Docker version 1.8.
        If the OpenShift version is 3.2 or 3.3, ensure Docker version 1.10.
        If the current OpenShift version is >= 3.4, ensure Docker version 1.12."""
        openshift_version = self.get_openshift_version(task_vars)

        if float(openshift_version) >= 3.4:
            return self.openshift_to_docker_version["3.4"]

        docker_version = self.openshift_to_docker_version.get(str(openshift_version))
        if docker_version:
            return docker_version

        msg = "There is no recommended version of Docker for the current version of OpenShift: {}"
        raise OpenShiftCheckException(msg.format(openshift_version))

    def get_openshift_version(self, task_vars):
        openshift_version = get_var(task_vars, "openshift_image_tag")
        if openshift_version and openshift_version[0] == 'v':
            openshift_version = openshift_version[1:]

        return self.parse_version(openshift_version)

    def parse_version(self, version):
        components = version.split(".")
        if not components or len(components) < 2:
            msg = "An invalid version of OpenShift was found for this host: {}"
            raise OpenShiftCheckException(msg.format(version))

        if components[0] in self.openshift_major_release_version:
            components[0] = self.openshift_major_release_version[components[0]]

        return '.'.join(components[:2])
