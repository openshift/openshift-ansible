"""
Mixin classes meant to be used with subclasses of OpenShiftCheck.
"""

from openshift_checks import get_var


class NotContainerizedMixin(object):
    """Mixin for checks that are only active when not in containerized mode."""
    # permanent # pylint: disable=too-few-public-methods
    # Reason: The mixin is not intended to stand on its own as a class.

    @classmethod
    def is_active(cls, task_vars):
        """Only run on non-containerized hosts."""
        is_containerized = get_var(task_vars, "openshift", "common", "is_containerized")
        return super(NotContainerizedMixin, cls).is_active(task_vars) and not is_containerized


class DockerHostMixin(object):
    """Mixin for checks that are only active on hosts that require Docker."""

    dependencies = []

    @classmethod
    def is_active(cls, task_vars):
        """Only run on hosts that depend on Docker."""
        is_containerized = get_var(task_vars, "openshift", "common", "is_containerized")
        is_node = "nodes" in get_var(task_vars, "group_names", default=[])
        return super(DockerHostMixin, cls).is_active(task_vars) and (is_containerized or is_node)

    def ensure_dependencies(self, task_vars):
        """
        Ensure that docker-related packages exist, but not on atomic hosts
        (which would not be able to install but should already have them).
        Returns: msg, failed, changed
        """
        if get_var(task_vars, "openshift", "common", "is_atomic"):
            return "", False, False

        # NOTE: we would use the "package" module but it's actually an action plugin
        # and it's not clear how to invoke one of those. This is about the same anyway:
        result = self.execute_module(
            get_var(task_vars, "ansible_pkg_mgr", default="yum"),
            {"name": self.dependencies, "state": "present"},
            task_vars=task_vars,
        )
        msg = result.get("msg", "")
        if result.get("failed"):
            if "No package matching" in msg:
                msg = "Ensure that all required dependencies can be installed via `yum`.\n"
            msg = (
                "Unable to install required packages on this host:\n"
                "    {deps}\n{msg}"
            ).format(deps=',\n    '.join(self.dependencies), msg=msg)
        failed = result.get("failed", False) or result.get("rc", 0) != 0
        changed = result.get("changed", False)
        return msg, failed, changed
