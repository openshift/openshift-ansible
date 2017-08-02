"""Check for an aggregated logging Curator deployment"""

from openshift_checks.logging.logging import LoggingCheck


class Curator(LoggingCheck):
    """Check for an aggregated logging Curator deployment"""

    name = "curator"
    tags = ["health", "logging"]

    def run(self):
        """Check various things and gather errors. Returns: result as hash"""

        self.logging_namespace = self.get_var("openshift_logging_namespace", default="logging")
        curator_pods, error = self.get_pods_for_component(
            self.logging_namespace,
            "curator",
        )
        if error:
            return {"failed": True, "changed": False, "msg": error}
        check_error = self.check_curator(curator_pods)

        if check_error:
            msg = ("The following Curator deployment issue was found:"
                   "{}".format(check_error))
            return {"failed": True, "changed": False, "msg": msg}

        # TODO(lmeyer): run it all again for the ops cluster
        return {"failed": False, "changed": False, "msg": 'No problems found with Curator deployment.'}

    def check_curator(self, pods):
        """Check to see if curator is up and working. Returns: error string"""
        if not pods:
            return (
                "There are no Curator pods for the logging stack,\n"
                "so nothing will prune Elasticsearch indexes.\n"
                "Is Curator correctly deployed?"
            )

        not_running = self.not_running_pods(pods)
        if len(not_running) == len(pods):
            return (
                "The Curator pod is not currently in a running state,\n"
                "so Elasticsearch indexes may increase without bound."
            )
        if len(pods) - len(not_running) > 1:
            return (
                "There is more than one Curator pod running. This should not normally happen.\n"
                "Although this doesn't cause any problems, you may want to investigate."
            )

        return None
