"""
Module for performing checks on an Fluentd logging deployment
"""

import json

from openshift_checks import get_var
from openshift_checks.logging.logging import LoggingCheck


class Fluentd(LoggingCheck):
    """Module that checks an integrated logging Fluentd deployment"""
    name = "fluentd"
    tags = ["health", "logging"]

    logging_namespace = None

    def run(self, tmp, task_vars):
        """Check various things and gather errors. Returns: result as hash"""

        self.logging_namespace = get_var(task_vars, "openshift_logging_namespace", default="logging")
        fluentd_pods, error = super(Fluentd, self).get_pods_for_component(
            self.execute_module,
            self.logging_namespace,
            "fluentd",
            task_vars,
        )
        if error:
            return {"failed": True, "changed": False, "msg": error}
        check_error = self.check_fluentd(fluentd_pods, task_vars)

        if check_error:
            msg = ("The following Fluentd deployment issue was found:"
                   "\n-------\n"
                   "{}".format(check_error))
            return {"failed": True, "changed": False, "msg": msg}

        # TODO(lmeyer): run it all again for the ops cluster
        return {"failed": False, "changed": False, "msg": 'No problems found with Fluentd deployment.'}

    @staticmethod
    def _filter_fluentd_labeled_nodes(nodes_by_name, node_selector):
        """Filter to all nodes with fluentd label. Returns dict(name: node), error string"""
        label, value = node_selector.split('=', 1)
        fluentd_nodes = {
            name: node for name, node in nodes_by_name.items()
            if node['metadata']['labels'].get(label) == value
        }
        if not fluentd_nodes:
            return None, (
                'There are no nodes with the fluentd label {label}.\n'
                'This means no logs will be aggregated from the nodes.'
            ).format(label=node_selector)
        return fluentd_nodes, None

    @staticmethod
    def _check_node_labeling(nodes_by_name, fluentd_nodes, node_selector, task_vars):
        """Note if nodes are not labeled as expected. Returns: error string"""
        intended_nodes = get_var(task_vars, 'openshift_logging_fluentd_hosts', default=['--all'])
        if not intended_nodes or '--all' in intended_nodes:
            intended_nodes = nodes_by_name.keys()
        nodes_missing_labels = set(intended_nodes) - set(fluentd_nodes.keys())
        if nodes_missing_labels:
            return (
                'The following nodes are supposed to be labeled with {label} but are not:\n'
                '  {nodes}\n'
                'Fluentd will not aggregate logs from these nodes.'
            ).format(label=node_selector, nodes=', '.join(nodes_missing_labels))
        return None

    @staticmethod
    def _check_nodes_have_fluentd(pods, fluentd_nodes):
        """Make sure fluentd is on all the labeled nodes. Returns: error string"""
        unmatched_nodes = fluentd_nodes.copy()
        node_names_by_label = {
            node['metadata']['labels']['kubernetes.io/hostname']: name
            for name, node in fluentd_nodes.items()
        }
        node_names_by_internal_ip = {
            address['address']: name
            for name, node in fluentd_nodes.items()
            for address in node['status']['addresses']
            if address['type'] == "InternalIP"
        }
        for pod in pods:
            for name in [
                    pod['spec']['nodeName'],
                    node_names_by_internal_ip.get(pod['spec']['nodeName']),
                    node_names_by_label.get(pod.get('spec', {}).get('host')),
            ]:
                unmatched_nodes.pop(name, None)
        if unmatched_nodes:
            return (
                'The following nodes are supposed to have a Fluentd pod but do not:\n'
                '{nodes}'
                'These nodes will not have their logs aggregated.'
            ).format(nodes=''.join(
                "  {}\n".format(name)
                for name in unmatched_nodes.keys()
            ))
        return None

    def _check_fluentd_pods_running(self, pods):
        """Make sure all fluentd pods are running. Returns: error string"""
        not_running = super(Fluentd, self).not_running_pods(pods)
        if not_running:
            return (
                'The following Fluentd pods are supposed to be running but are not:\n'
                '{pods}'
                'These pods will not aggregate logs from their nodes.'
            ).format(pods=''.join(
                "  {} ({})\n".format(pod['metadata']['name'], pod['spec'].get('host', 'None'))
                for pod in not_running
            ))
        return None

    def check_fluentd(self, pods, task_vars):
        """Verify fluentd is running everywhere. Returns: error string"""

        node_selector = get_var(task_vars, 'openshift_logging_fluentd_nodeselector',
                                default='logging-infra-fluentd=true')

        nodes_by_name, error = self.get_nodes_by_name(task_vars)

        if error:
            return error
        fluentd_nodes, error = self._filter_fluentd_labeled_nodes(nodes_by_name, node_selector)
        if error:
            return error

        error_msgs = []
        error = self._check_node_labeling(nodes_by_name, fluentd_nodes, node_selector, task_vars)
        if error:
            error_msgs.append(error)
        error = self._check_nodes_have_fluentd(pods, fluentd_nodes)
        if error:
            error_msgs.append(error)
        error = self._check_fluentd_pods_running(pods)
        if error:
            error_msgs.append(error)

        # Make sure there are no extra fluentd pods
        if len(pods) > len(fluentd_nodes):
            error_msgs.append(
                'There are more Fluentd pods running than nodes labeled.\n'
                'This may not cause problems with logging but it likely indicates something wrong.'
            )

        return '\n'.join(error_msgs)

    def get_nodes_by_name(self, task_vars):
        """Retrieve all the node definitions. Returns: dict(name: node), error string"""
        nodes_json = self._exec_oc("get nodes -o json", [], task_vars)
        try:
            nodes = json.loads(nodes_json)
        except ValueError:  # no valid json - should not happen
            return None, "Could not obtain a list of nodes to validate fluentd. Output from oc get:\n" + nodes_json
        if not nodes or not nodes.get('items'):  # also should not happen
            return None, "No nodes appear to be defined according to the API."
        return {
            node['metadata']['name']: node
            for node in nodes['items']
        }, None

    def _exec_oc(self, cmd_str, extra_args, task_vars):
        return super(Fluentd, self).exec_oc(self.execute_module,
                                            self.logging_namespace,
                                            cmd_str,
                                            extra_args,
                                            task_vars)
