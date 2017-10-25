"""Check auto-discovery entry for an external connectivity check."""

from openshift_checks import OpenShiftCheck


class ConnectivityExternal(OpenShiftCheck):
    """Check is not managed here. It is an ansible playbook."""

    name = "connectivity"
    tags = ["pre-flight", "connectivity"]

    def is_active(self):
        """It is always active as externally managed."""
        return super(ConnectivityExternal, self).is_active()

    def run(self):
        # TODO(bogdando) implement an ansible playbook call
        # for the external playbook. For now, it is included
        # elsewhere
        self.register_log("Not implemented",
                          "Use ansible to invoke this connectivity check")
        return {}
