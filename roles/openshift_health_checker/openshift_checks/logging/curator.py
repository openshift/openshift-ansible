"""Check for an aggregated logging Curator cronjob"""

from openshift_checks.logging.logging import OpenShiftCheckException, LoggingCheck


class Curator(LoggingCheck):
    """Check for an aggregated logging Curator cronjob"""

    name = "curator"
    tags = ["health", "logging"]

    def run(self):
        """Check various things and gather errors. Returns: result as hash"""

        cronjobs = self.get_cronjobs_for_component("curator")
        if not cronjobs:
            raise OpenShiftCheckException(
                "MissingComponentCronJobs",
                "There are no Curator cronjobs for the logging stack,\n"
                "so nothing will prune Elasticsearch indexes.\n"
                "Is Curator correctly deployed?"
            )

        return {}
