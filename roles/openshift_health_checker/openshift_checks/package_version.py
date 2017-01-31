# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, OpenShiftCheckException
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
        try:
            openshift_release = task_vars["openshift_release"]
        except (KeyError, TypeError):
            raise OpenShiftCheckException("'openshift_release' is undefined")

        args = {"version": openshift_release}
        return self.module_executor("aos_version", args, tmp, task_vars)
