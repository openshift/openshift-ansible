# pylint: disable=missing-docstring,too-few-public-methods
"""
Mixin classes meant to be used with subclasses of OpenShiftCheck.
"""

from openshift_checks import get_var


class NotContainerizedMixin(object):
    """Mixin for checks that are only active when not in containerized mode."""

    @classmethod
    def is_active(cls, task_vars):
        is_containerized = get_var(task_vars, "openshift", "common", "is_containerized")
        return super(NotContainerizedMixin, cls).is_active(task_vars) and not is_containerized
