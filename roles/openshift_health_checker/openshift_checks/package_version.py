# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, get_var
from openshift_checks.mixins import NotContainerized


class PackageVersion(NotContainerized, OpenShiftCheck):
    """Check that available RPM packages match the required versions."""

    name = "package_version"
    tags = ["preflight"]

    @classmethod
    def is_active(cls, task_vars):
        return (
            super(PackageVersion, cls).is_active(task_vars)
            and task_vars.get("deployment_type") == "openshift-enterprise"
        )

    def run(self, tmp, task_vars):
        openshift_release = get_var(task_vars, "openshift_release")

        args = {"version": openshift_release}
        return self.module_executor("aos_version", args, tmp, task_vars)
