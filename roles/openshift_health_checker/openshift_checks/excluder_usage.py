# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, get_var, normalized_minor_release
from openshift_checks.mixins import NotContainerizedMixin


class ExcluderUsage(NotContainerizedMixin, OpenShiftCheck):
    """Check that required RPM packages are available."""

    name = "excluder_usage"
    tags = ["preflight", "preupgrade", "health"]

    def run(self, tmp, task_vars):
        args = {
            "rpm_prefix": get_var(task_vars, "openshift", "common", "service_type"), #origin/atomic-openshift
            "openshift_release": normalized_minor_release(task_vars),
        }
        return self.module_executor(
                module_name=ExcluderUsage.name,
                module_args=args,
                tmp=tmp,
                task_vars=task_vars,
            )

