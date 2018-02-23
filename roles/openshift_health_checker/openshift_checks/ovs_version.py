"""
Ansible module for determining if an installed version of Open vSwitch is incompatible with the
currently installed version of OpenShift.
"""

from openshift_checks import OpenShiftCheck
from openshift_checks.mixins import NotContainerizedMixin


class OvsVersion(NotContainerizedMixin, OpenShiftCheck):
    """Check that packages in a package_list are installed on the host
    and are the correct version as determined by an OpenShift installation.
    """

    name = "ovs_version"
    tags = ["health"]

    openshift_to_ovs_version = {
        (3, 4): "2.4",
        (3, 5): ["2.6", "2.7"],
        (3, 6): ["2.6", "2.7", "2.8", "2.9"],
        (3, 7): ["2.6", "2.7", "2.8", "2.9"],
        (3, 8): ["2.6", "2.7", "2.8", "2.9"],
        (3, 9): ["2.6", "2.7", "2.8", "2.9"],
        (3, 10): ["2.6", "2.7", "2.8", "2.9"],
    }

    def is_active(self):
        """Skip hosts that do not have package requirements."""
        group_names = self.get_var("group_names", default=[])
        master_or_node = 'oo_masters_to_config' in group_names or 'oo_nodes_to_config' in group_names
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
        """Return the correct Open vSwitch version(s) for the current OpenShift version."""
        return self.get_required_version("Open vSwitch", self.openshift_to_ovs_version)
