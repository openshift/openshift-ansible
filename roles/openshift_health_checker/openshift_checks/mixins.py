"""
Mixin classes meant to be used with subclasses of OpenShiftCheck.
"""


class NotContainerizedMixin(object):
    """Mixin for checks that are only active when not in containerized mode."""
    # permanent # pylint: disable=too-few-public-methods
    # Reason: The mixin is not intended to stand on its own as a class.

    def is_active(self):
        """Only run on non-containerized hosts."""
        openshift_is_atomic = self.get_var("openshift_is_atomic")
        return super(NotContainerizedMixin, self).is_active() and not openshift_is_atomic


class DockerHostMixin(object):
    """Mixin for checks that are only active on hosts that require Docker."""
    # permanent # pylint: disable=too-few-public-methods
    # Reason: The mixin is not intended to stand on its own as a class.

    def is_active(self):
        """Only run on hosts that depend on Docker."""
        group_names = set(self.get_var("group_names", default=[]))
        needs_docker = set(["oo_nodes_to_config"])
        return super(DockerHostMixin, self).is_active() and bool(group_names.intersection(needs_docker))
