"""Check that available RPM packages match the required versions."""

from openshift_checks import OpenShiftCheck
from openshift_checks.mixins import NotContainerizedMixin


class PackageVersion(NotContainerizedMixin, OpenShiftCheck):
    """Check that available RPM packages match the required versions."""

    name = "package_version"
    tags = ["preflight"]

    # NOTE: versions outside those specified are mapped to least/greatest
    openshift_to_ovs_version = {
        (3, 4): "2.4",
        (3, 5): ["2.6", "2.7"],
        (3, 6): ["2.6", "2.7", "2.8"],
        (3, 7): ["2.6", "2.7", "2.8"],
        (3, 8): ["2.6", "2.7", "2.8"],
        (3, 9): ["2.6", "2.7", "2.8"],
    }

    openshift_to_docker_version = {
        (3, 1): "1.8",
        (3, 2): "1.10",
        (3, 3): "1.10",
        (3, 4): "1.12",
        (3, 5): "1.12",
        (3, 6): "1.12",
        (3, 7): "1.12",
        (3, 8): "1.12",
        (3, 9): ["1.12", "1.13"],
    }

    def is_active(self):
        """Skip hosts that do not have package requirements."""
        group_names = self.get_var("group_names", default=[])
        master_or_node = 'oo_masters_to_config' in group_names or 'oo_nodes_to_config' in group_names
        return super(PackageVersion, self).is_active() and master_or_node

    def run(self):
        rpm_prefix = self.get_var("openshift_service_type")
        if self._templar is not None:
            rpm_prefix = self._templar.template(rpm_prefix)
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
        return self.get_required_version("Open vSwitch", self.openshift_to_ovs_version)

    def get_required_docker_version(self):
        """Return the correct Docker version(s) for the current OpenShift version."""
        return self.get_required_version("Docker", self.openshift_to_docker_version)
