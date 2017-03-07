# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, get_var, normalized_release
from openshift_checks.mixins import NotContainerizedMixin


class PackageVersion(NotContainerizedMixin, OpenShiftCheck):
    """Check that available RPM packages match the required versions."""

    name = "package_version"
    tags = ["preflight"]

    def run(self, tmp, task_vars):
        args = {
            "prefix": get_var(task_vars, "openshift", "common", "service_type"), 
            "version": normalized_release(task_vars),
        }
        return self.module_executor("aos_version", args, tmp, task_vars)
