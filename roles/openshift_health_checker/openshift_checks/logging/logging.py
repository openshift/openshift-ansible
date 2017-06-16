"""
Util functions for performing checks on an Elasticsearch, Fluentd, and Kibana stack
"""

import json
import os

from openshift_checks import OpenShiftCheck, OpenShiftCheckException


class LoggingCheck(OpenShiftCheck):
    """Base class for OpenShift aggregated logging component checks"""

    name = "logging"
    logging_namespace = "logging"

    def is_active(self):
        logging_deployed = self.get_var("openshift_hosted_logging_deploy", default=False)
        return logging_deployed and super(LoggingCheck, self).is_active() and self.is_first_master()

    def is_first_master(self):
        """Determine if running on first master. Returns: bool"""
        # Note: It would be nice to use membership in oo_first_master group, however for now it
        # seems best to avoid requiring that setup and just check this is the first master.
        hostname = self.get_var("ansible_ssh_host") or [None]
        masters = self.get_var("groups", "masters", default=None) or [None]
        return masters[0] == hostname

    def run(self):
        pass

    def get_pods_for_component(self, namespace, logging_component):
        """Get all pods for a given component. Returns: list of pods for component, error string"""
        pod_output = self.exec_oc(
            namespace,
            "get pods -l component={} -o json".format(logging_component),
            [],
        )
        try:
            pods = json.loads(pod_output)
            if not pods or not pods.get('items'):
                raise ValueError()
        except ValueError:
            # successful run but non-parsing data generally means there were no pods in the namespace
            return None, 'No pods were found for the "{}" logging component.'.format(logging_component)

        return pods['items'], None

    @staticmethod
    def not_running_pods(pods):
        """Returns: list of pods not in a ready and running state"""
        return [
            pod for pod in pods
            if not pod.get("status", {}).get("containerStatuses") or any(
                container['ready'] is False
                for container in pod['status']['containerStatuses']
            ) or not any(
                condition['type'] == 'Ready' and condition['status'] == 'True'
                for condition in pod['status'].get('conditions', [])
            )
        ]

    def exec_oc(self, namespace="logging", cmd_str="", extra_args=None):
        """
        Execute an 'oc' command in the remote host.
        Returns: output of command and namespace,
        or raises OpenShiftCheckException on error
        """
        config_base = self.get_var("openshift", "common", "config_base")
        args = {
            "namespace": namespace,
            "config_file": os.path.join(config_base, "master", "admin.kubeconfig"),
            "cmd": cmd_str,
            "extra_args": list(extra_args) if extra_args else [],
        }

        result = self.execute_module("ocutil", args)
        if result.get("failed"):
            msg = (
                'Unexpected error using `oc` to validate the logging stack components.\n'
                'Error executing `oc {cmd}`:\n'
                '{error}'
            ).format(cmd=args['cmd'], error=result['result'])

            if result['result'] == '[Errno 2] No such file or directory':
                msg = (
                    "This host is supposed to be a master but does not have the `oc` command where expected.\n"
                    "Has an installation been run on this host yet?"
                )
            raise OpenShiftCheckException(msg)

        return result.get("result", "")
