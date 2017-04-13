# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, get_var
from openshift_checks.mixins import NotContainerizedMixin


class PackageVersion(NotContainerizedMixin, OpenShiftCheck):
    """Check that available RPM packages match the required versions."""

    name = "package_version"
    tags = ["preflight"]

    @classmethod
    def is_active(cls, task_vars):
        """Skip hosts that do not have package requirements."""
        group_names = get_var(task_vars, "group_names", default=[])
        master_or_node = 'masters' in group_names or 'nodes' in group_names
        return super(PackageVersion, cls).is_active(task_vars) and master_or_node

    def run(self, tmp, task_vars):
        args = {
            "requested_openshift_release": get_var(task_vars, "openshift_release", default=''),
            "openshift_deployment_type": get_var(task_vars, "openshift_deployment_type"),
            "rpm_prefix": get_var(task_vars, "openshift", "common", "service_type"),
        }
        return self.execute_module("aos_version", args, tmp, task_vars)
