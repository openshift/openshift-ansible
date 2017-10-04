"""Check that available RPM packages match the required versions."""

import re

from openshift_checks import OpenShiftCheck, OpenShiftCheckException
from openshift_checks.mixins import NotContainerizedMixin


class PackageVersion(NotContainerizedMixin, OpenShiftCheck):
    """Check that available RPM packages match the required versions."""

    name = "package_version"
    tags = ["preflight"]

    # NOTE: versions outside those specified are mapped to least/greatest
    openshift_to_ovs_version = {
        (3, 4): "2.4",
        (3, 5): ["2.6", "2.7"],
        (3, 6): ["2.6", "2.7"],
    }

    openshift_to_docker_version = {
        (3, 1): "1.8",
        (3, 2): "1.10",
        (3, 3): "1.10",
        (3, 4): "1.12",
        (3, 5): "1.12",
        (3, 6): "1.12",
    }

    # map major OpenShift release versions across releases to a common major version
    map_major_release_version = {
        1: 3,
    }

    def is_active(self):
        """Skip hosts that do not have package requirements."""
        group_names = self.get_var("group_names", default=[])
        master_or_node = 'oo_masters_to_config' in group_names or 'oo_nodes_to_config' in group_names
        return super(PackageVersion, self).is_active() and master_or_node

    def run(self):
        rpm_prefix = self.get_var("openshift", "common", "service_type")
        openshift_release = self.get_var("openshift_release", default='')
        deployment_type = self.get_var("openshift_deployment_type")
        check_multi_minor_release = deployment_type in ['openshift-enterprise']

        args = {
            "package_mgr": self.get_var("ansible_pkg_mgr"),
            "package_list": [
                {
                    "name": "openvswitch",
                    "version": self.get_required_ovs_version(),
                    "check_multi": False,
                },
                {
                    "name": "docker",
                    "version": self.get_required_docker_version(),
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

        return self.execute_module_with_retries("aos_version", args)

    def get_required_ovs_version(self):
        """Return the correct Open vSwitch version(s) for the current OpenShift version."""
        openshift_version = self.get_openshift_version_tuple()

        earliest = min(self.openshift_to_ovs_version)
        latest = max(self.openshift_to_ovs_version)
        if openshift_version < earliest:
            return self.openshift_to_ovs_version[earliest]
        if openshift_version > latest:
            return self.openshift_to_ovs_version[latest]

        ovs_version = self.openshift_to_ovs_version.get(openshift_version)
        if not ovs_version:
            msg = "There is no recommended version of Open vSwitch for the current version of OpenShift: {}"
            raise OpenShiftCheckException(msg.format(".".join(str(comp) for comp in openshift_version)))

        return ovs_version

    def get_required_docker_version(self):
        """Return the correct Docker version(s) for the current OpenShift version."""
        openshift_version = self.get_openshift_version_tuple()

        earliest = min(self.openshift_to_docker_version)
        latest = max(self.openshift_to_docker_version)
        if openshift_version < earliest:
            return self.openshift_to_docker_version[earliest]
        if openshift_version > latest:
            return self.openshift_to_docker_version[latest]

        docker_version = self.openshift_to_docker_version.get(openshift_version)
        if not docker_version:
            msg = "There is no recommended version of Docker for the current version of OpenShift: {}"
            raise OpenShiftCheckException(msg.format(".".join(str(comp) for comp in openshift_version)))

        return docker_version

    def get_openshift_version_tuple(self):
        """Return received image tag as a normalized (X, Y) minor version tuple."""
        version = self.get_var("openshift_image_tag")
        comps = [int(component) for component in re.findall(r'\d+', version)]

        if len(comps) < 2:
            msg = "An invalid version of OpenShift was found for this host: {}"
            raise OpenShiftCheckException(msg.format(version))

        comps[0] = self.map_major_release_version.get(comps[0], comps[0])
        return tuple(comps[0:2])
