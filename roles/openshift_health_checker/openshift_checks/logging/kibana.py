"""
Module for performing checks on a Kibana logging deployment
"""

import json
import ssl

try:
    from urllib2 import HTTPError, URLError
    import urllib2
except ImportError:
    from urllib.error import HTTPError, URLError
    import urllib.request as urllib2

from openshift_checks import get_var
from openshift_checks.logging.logging import LoggingCheck


class Kibana(LoggingCheck):
    """Module that checks an integrated logging Kibana deployment"""

    name = "kibana"
    tags = ["health", "logging"]

    logging_namespace = None

    def run(self, tmp, task_vars):
        """Check various things and gather errors. Returns: result as hash"""

        self.logging_namespace = get_var(task_vars, "openshift_logging_namespace", default="logging")
        kibana_pods, error = super(Kibana, self).get_pods_for_component(
            self.execute_module,
            self.logging_namespace,
            "kibana",
            task_vars,
        )
        if error:
            return {"failed": True, "changed": False, "msg": error}
        check_error = self.check_kibana(kibana_pods)

        if not check_error:
            check_error = self._check_kibana_route(task_vars)

        if check_error:
            msg = ("The following Kibana deployment issue was found:"
                   "\n-------\n"
                   "{}".format(check_error))
            return {"failed": True, "changed": False, "msg": msg}

        # TODO(lmeyer): run it all again for the ops cluster
        return {"failed": False, "changed": False, "msg": 'No problems found with Kibana deployment.'}

    def _verify_url_internal(self, url, task_vars):
        """
        Try to reach a URL from the host.
        Returns: success (bool), reason (for failure)
        """
        args = dict(
            url=url,
            follow_redirects='none',
            validate_certs='no',  # likely to be signed with internal CA
            # TODO(lmeyer): give users option to validate certs
            status_code=302,
        )
        result = self.execute_module('uri', args, task_vars)
        if result.get('failed'):
            return result['msg']
        return None

    @staticmethod
    def _verify_url_external(url):
        """
        Try to reach a URL from ansible control host.
        Returns: success (bool), reason (for failure)
        """
        # This actually checks from the ansible control host, which may or may not
        # really be "external" to the cluster.

        # Disable SSL cert validation to work around internally signed certs
        ctx = ssl.create_default_context()
        ctx.check_hostname = False  # or setting CERT_NONE is refused
        ctx.verify_mode = ssl.CERT_NONE

        # Verify that the url is returning a valid response
        try:
            # We only care if the url connects and responds
            return_code = urllib2.urlopen(url, context=ctx).getcode()
        except HTTPError as httperr:
            return httperr.reason
        except URLError as urlerr:
            return str(urlerr)

        # there appears to be no way to prevent urlopen from following redirects
        if return_code != 200:
            return 'Expected success (200) but got return code {}'.format(int(return_code))

        return None

    def check_kibana(self, pods):
        """Check to see if Kibana is up and working. Returns: error string."""

        if not pods:
            return "There are no Kibana pods deployed, so no access to the logging UI."

        not_running = self.not_running_pods(pods)
        if len(not_running) == len(pods):
            return "No Kibana pod is in a running state, so there is no access to the logging UI."
        elif not_running:
            return (
                "The following Kibana pods are not currently in a running state:\n"
                "{pods}"
                "However at least one is, so service may not be impacted."
            ).format(pods="".join("  " + pod['metadata']['name'] + "\n" for pod in not_running))

        return None

    def _get_kibana_url(self, task_vars):
        """
        Get kibana route or report error.
        Returns: url (or empty), reason for failure
        """

        # Get logging url
        get_route = self._exec_oc("get route logging-kibana -o json", [], task_vars)
        if not get_route:
            return None, 'no_route_exists'

        route = json.loads(get_route)

        # check that the route has been accepted by a router
        ingress = route["status"]["ingress"]
        # ingress can be null if there is no router, or empty if not routed
        if not ingress or not ingress[0]:
            return None, 'route_not_accepted'

        host = route.get("spec", {}).get("host")
        if not host:
            return None, 'route_missing_host'

        return 'https://{}/'.format(host), None

    def _check_kibana_route(self, task_vars):
        """
        Check to see if kibana route is up and working.
        Returns: error string
        """
        known_errors = dict(
            no_route_exists=(
                'No route is defined for Kibana in the logging namespace,\n'
                'so the logging stack is not accessible. Is logging deployed?\n'
                'Did something remove the logging-kibana route?'
            ),
            route_not_accepted=(
                'The logging-kibana route is not being routed by any router.\n'
                'Is the router deployed and working?'
            ),
            route_missing_host=(
                'The logging-kibana route has no hostname defined,\n'
                'which should never happen. Did something alter its definition?'
            ),
        )

        kibana_url, error = self._get_kibana_url(task_vars)
        if not kibana_url:
            return known_errors.get(error, error)

        # first, check that kibana is reachable from the master.
        error = self._verify_url_internal(kibana_url, task_vars)
        if error:
            if 'urlopen error [Errno 111] Connection refused' in error:
                error = (
                    'Failed to connect from this master to Kibana URL {url}\n'
                    'Is kibana running, and is at least one router routing to it?'
                ).format(url=kibana_url)
            elif 'urlopen error [Errno -2] Name or service not known' in error:
                error = (
                    'Failed to connect from this master to Kibana URL {url}\n'
                    'because the hostname does not resolve.\n'
                    'Is DNS configured for the Kibana hostname?'
                ).format(url=kibana_url)
            elif 'Status code was not' in error:
                error = (
                    'A request from this master to the Kibana URL {url}\n'
                    'did not return the correct status code (302).\n'
                    'This could mean that Kibana is malfunctioning, the hostname is\n'
                    'resolving incorrectly, or other network issues. The output was:\n'
                    '  {error}'
                ).format(url=kibana_url, error=error)
            return 'Error validating the logging Kibana route:\n' + error

        # in production we would like the kibana route to work from outside the
        # cluster too; but that may not be the case, so allow disabling just this part.
        if not get_var(task_vars, "openshift_check_efk_kibana_external", default=True):
            return None
        error = self._verify_url_external(kibana_url)
        if error:
            if 'urlopen error [Errno 111] Connection refused' in error:
                error = (
                    'Failed to connect from the Ansible control host to Kibana URL {url}\n'
                    'Is the router for the Kibana hostname exposed externally?'
                ).format(url=kibana_url)
            elif 'urlopen error [Errno -2] Name or service not known' in error:
                error = (
                    'Failed to resolve the Kibana hostname in {url}\n'
                    'from the Ansible control host.\n'
                    'Is DNS configured to resolve this Kibana hostname externally?'
                ).format(url=kibana_url)
            elif 'Expected success (200)' in error:
                error = (
                    'A request to Kibana at {url}\n'
                    'returned the wrong error code:\n'
                    '  {error}\n'
                    'This could mean that Kibana is malfunctioning, the hostname is\n'
                    'resolving incorrectly, or other network issues.'
                ).format(url=kibana_url, error=error)
            error = (
                'Error validating the logging Kibana route:\n{error}\n'
                'To disable external Kibana route validation, set in your inventory:\n'
                '  openshift_check_efk_kibana_external=False'
            ).format(error=error)
            return error
        return None

    def _exec_oc(self, cmd_str, extra_args, task_vars):
        return super(Kibana, self).exec_oc(self.execute_module,
                                           self.logging_namespace,
                                           cmd_str,
                                           extra_args,
                                           task_vars)
