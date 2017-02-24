# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, get_var
from openshift_checks.mixins import NotContainerizedMixin


class PackageVersion(NotContainerizedMixin, OpenShiftCheck):
    """Check that available RPM packages match the required versions."""

    name = "package_version"
    tags = ["preflight"]

    def run(self, tmp, task_vars):
        rpm_prefix = get_var(task_vars, "openshift", "common", "service_type")
        openshift_release = get_var(task_vars, "openshift_release")

        args = {
            "prefix": rpm_prefix,
            "version": openshift_release,
        }
        return self.module_executor("aos_version", args, tmp, task_vars)
