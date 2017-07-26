"""
Ansible module for determining if an installed version of Open vSwitch is incompatible with the
currently installed version of OpenShift.
"""

from openshift_checks import OpenShiftCheck, OpenShiftCheckException
from openshift_checks.mixins import NotContainerizedMixin


class OvsVersion(NotContainerizedMixin, OpenShiftCheck):
    """Check that packages in a package_list are installed on the host
    and are the correct version as determined by an OpenShift installation.
    """

    name = "ovs_version"
    tags = ["health"]

    openshift_to_ovs_version = {
        "3.6": "2.6",
        "3.5": "2.6",
        "3.4": "2.4",
    }

    # map major release versions across releases
    # to a common major version
    openshift_major_release_version = {
        "1": "3",
    }

    def is_active(self):
        """Skip hosts that do not have package requirements."""
        group_names = self.get_var("group_names", default=[])
        master_or_node = 'masters' in group_names or 'nodes' in group_names
        return super(OvsVersion, self).is_active() and master_or_node

    def run(self):
        args = {
            "package_list": [
                {
                    "name": "openvswitch",
                    "version": self.get_required_ovs_version(),
                },
            ],
        }
        return self.execute_module("rpm_version", args)

    def get_required_ovs_version(self):
        """Return the correct Open vSwitch version for the current OpenShift version"""
        openshift_version = self._get_openshift_version()

        if float(openshift_version) < 3.5:
            return self.openshift_to_ovs_version["3.4"]

        ovs_version = self.openshift_to_ovs_version.get(str(openshift_version))
        if ovs_version:
            return self.openshift_to_ovs_version[str(openshift_version)]

        msg = "There is no recommended version of Open vSwitch for the current version of OpenShift: {}"
        raise OpenShiftCheckException(msg.format(openshift_version))

    def _get_openshift_version(self):
        openshift_version = self.get_var("openshift_image_tag")
        if openshift_version and openshift_version[0] == 'v':
            openshift_version = openshift_version[1:]

        return self._parse_version(openshift_version)

    def _parse_version(self, version):
        components = version.split(".")
        if not components or len(components) < 2:
            msg = "An invalid version of OpenShift was found for this host: {}"
            raise OpenShiftCheckException(msg.format(version))

        if components[0] in self.openshift_major_release_version:
            components[0] = self.openshift_major_release_version[components[0]]

        return '.'.join(components[:2])
