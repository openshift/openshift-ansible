# pylint: disable=missing-docstring
from openshift_checks import get_var


class NotContainerized(object):
    """Mixin for checks that are only active when not in containerized mode."""

    @classmethod
    def is_active(cls, task_vars):
        return (
            # This mixin is meant to be used with subclasses of
            # OpenShiftCheck. Pylint disables this by default on mixins,
            # though it relies on the class name ending in 'mixin'.
            # pylint: disable=no-member
            super(NotContainerized, cls).is_active(task_vars) and
            not cls.is_containerized(task_vars)
        )

    @staticmethod
    def is_containerized(task_vars):
        return get_var(task_vars, "openshift", "common", "is_containerized")
