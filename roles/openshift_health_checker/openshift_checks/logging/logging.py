"""
Util functions for performing checks on an Elasticsearch, Fluentd, and Kibana stack
"""

import json
import os

from openshift_checks import OpenShiftCheck, OpenShiftCheckException, get_var


class LoggingCheck(OpenShiftCheck):
    """Base class for logging component checks"""

    name = "logging"

    @classmethod
    def is_active(cls, task_vars):
        return super(LoggingCheck, cls).is_active(task_vars) and cls.is_first_master(task_vars)

    @staticmethod
    def is_first_master(task_vars):
        """Run only on first master and only when logging is configured. Returns: bool"""
        logging_deployed = get_var(task_vars, "openshift_hosted_logging_deploy", default=True)
        # Note: It would be nice to use membership in oo_first_master group, however for now it
        # seems best to avoid requiring that setup and just check this is the first master.
        hostname = get_var(task_vars, "ansible_ssh_host") or [None]
        masters = get_var(task_vars, "groups", "masters", default=None) or [None]
        return logging_deployed and masters[0] == hostname

    def run(self, tmp, task_vars):
        pass

    def get_pods_for_component(self, execute_module, namespace, logging_component, task_vars):
        """Get all pods for a given component. Returns: list of pods for component, error string"""
        pod_output = self.exec_oc(
            execute_module,
            namespace,
            "get pods -l component={} -o json".format(logging_component),
            [],
            task_vars
        )
        try:
            pods = json.loads(pod_output)
            if not pods or not pods.get('items'):
                raise ValueError()
        except ValueError:
            # successful run but non-parsing data generally means there were no pods in the namespace
            return None, 'There are no pods in the {} namespace. Is logging deployed?'.format(namespace)

        return pods['items'], None

    @staticmethod
    def not_running_pods(pods):
        """Returns: list of pods not in a ready and running state"""
        return [
            pod for pod in pods
            if any(
                container['ready'] is False
                for container in pod['status']['containerStatuses']
            ) or not any(
                condition['type'] == 'Ready' and condition['status'] == 'True'
                for condition in pod['status']['conditions']
            )
        ]

    @staticmethod
    def exec_oc(execute_module=None, namespace="logging", cmd_str="", extra_args=None, task_vars=None):
        """
        Execute an 'oc' command in the remote host.
        Returns: output of command and namespace,
        or raises OpenShiftCheckException on error
        """
        config_base = get_var(task_vars, "openshift", "common", "config_base")
        args = {
            "namespace": namespace,
            "config_file": os.path.join(config_base, "master", "admin.kubeconfig"),
            "cmd": cmd_str,
            "extra_args": list(extra_args) if extra_args else [],
        }

        result = execute_module("ocutil", args, task_vars)
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
