# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck
from openshift_checks.mixins import NotContainerized


class PackageUpdate(NotContainerized, OpenShiftCheck):
    """Check that there are no conflicts in RPM packages."""

    name = "package_update"
    tags = ["preflight"]

    def run(self, tmp, task_vars):
        args = {"packages": []}
        return self.module_executor("check_yum_update", args, tmp, task_vars)
