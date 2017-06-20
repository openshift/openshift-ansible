"""
Check for ensuring logs from pods can be queried in a reasonable amount of time.
"""

import json
import time

from uuid import uuid4

from openshift_checks import get_var, OpenShiftCheckException
from openshift_checks.logging.logging import LoggingCheck


ES_CMD_TIMEOUT_SECONDS = 30


class LoggingIndexTime(LoggingCheck):
    """Check that pod logs are aggregated and indexed in ElasticSearch within a reasonable amount of time."""
    name = "logging_index_time"
    tags = ["health", "logging"]

    logging_namespace = "logging"

    def run(self, tmp, task_vars):
        """Add log entry by making unique request to Kibana. Check for unique entry in the ElasticSearch pod logs."""
        try:
            log_index_timeout = int(
                get_var(task_vars, "openshift_check_logging_index_timeout_seconds", default=ES_CMD_TIMEOUT_SECONDS)
            )
        except ValueError:
            return {
                "failed": True,
                "msg": ('Invalid value provided for "openshift_check_logging_index_timeout_seconds". '
                        'Value must be an integer representing an amount in seconds.'),
            }

        running_component_pods = dict()

        # get all component pods
        self.logging_namespace = get_var(task_vars, "openshift_logging_namespace", default=self.logging_namespace)
        for component, name in (['kibana', 'Kibana'], ['es', 'Elasticsearch']):
            pods, error = self.get_pods_for_component(
                self.execute_module, self.logging_namespace, component, task_vars,
            )

            if error:
                msg = 'Unable to retrieve pods for the {} logging component: {}'
                return {"failed": True, "changed": False, "msg": msg.format(name, error)}

            running_pods = self.running_pods(pods)

            if not running_pods:
                msg = ('No {} pods in the "Running" state were found.'
                       'At least one pod is required in order to perform this check.')
                return {"failed": True, "changed": False, "msg": msg.format(name)}

            running_component_pods[component] = running_pods

        uuid = self.curl_kibana_with_uuid(running_component_pods["kibana"][0], task_vars)
        self.wait_until_cmd_or_err(running_component_pods["es"][0], uuid, log_index_timeout, task_vars)
        return {}

    def wait_until_cmd_or_err(self, es_pod, uuid, timeout_secs, task_vars):
        """Retry an Elasticsearch query every second until query success, or a defined
        length of time has passed."""
        deadline = time.time() + timeout_secs
        interval = 1
        while not self.query_es_from_es(es_pod, uuid, task_vars):
            if time.time() + interval > deadline:
                msg = "expecting match in Elasticsearch for message with uuid {}, but no matches were found after {}s."
                raise OpenShiftCheckException(msg.format(uuid, timeout_secs))
            time.sleep(interval)

    def curl_kibana_with_uuid(self, kibana_pod, task_vars):
        """curl Kibana with a unique uuid."""
        uuid = self.generate_uuid()
        pod_name = kibana_pod["metadata"]["name"]
        exec_cmd = "exec {pod_name} -c kibana -- curl --max-time 30 -s http://localhost:5601/{uuid}"
        exec_cmd = exec_cmd.format(pod_name=pod_name, uuid=uuid)

        error_str = self.exec_oc(self.execute_module, self.logging_namespace, exec_cmd, [], task_vars)

        try:
            error_code = json.loads(error_str)["statusCode"]
        except KeyError:
            msg = ('invalid response returned from Kibana request (Missing "statusCode" key):\n'
                   'Command: {}\nResponse: {}').format(exec_cmd, error_str)
            raise OpenShiftCheckException(msg)
        except ValueError:
            msg = ('invalid response returned from Kibana request (Non-JSON output):\n'
                   'Command: {}\nResponse: {}').format(exec_cmd, error_str)
            raise OpenShiftCheckException(msg)

        if error_code != 404:
            msg = 'invalid error code returned from Kibana request. Expecting error code "404", but got "{}" instead.'
            raise OpenShiftCheckException(msg.format(error_code))

        return uuid

    def query_es_from_es(self, es_pod, uuid, task_vars):
        """curl the Elasticsearch pod and look for a unique uuid in its logs."""
        pod_name = es_pod["metadata"]["name"]
        exec_cmd = (
            "exec {pod_name} -- curl --max-time 30 -s -f "
            "--cacert /etc/elasticsearch/secret/admin-ca "
            "--cert /etc/elasticsearch/secret/admin-cert "
            "--key /etc/elasticsearch/secret/admin-key "
            "https://logging-es:9200/project.{namespace}*/_count?q=message:{uuid}"
        )
        exec_cmd = exec_cmd.format(pod_name=pod_name, namespace=self.logging_namespace, uuid=uuid)
        result = self.exec_oc(self.execute_module, self.logging_namespace, exec_cmd, [], task_vars)

        try:
            count = json.loads(result)["count"]
        except KeyError:
            msg = 'invalid response from Elasticsearch query:\n"{}"\nMissing "count" key:\n{}'
            raise OpenShiftCheckException(msg.format(exec_cmd, result))
        except ValueError:
            msg = 'invalid response from Elasticsearch query:\n"{}"\nNon-JSON output:\n{}'
            raise OpenShiftCheckException(msg.format(exec_cmd, result))

        return count

    @staticmethod
    def running_pods(pods):
        """Filter pods that are running."""
        return [pod for pod in pods if pod['status']['phase'] == 'Running']

    @staticmethod
    def generate_uuid():
        """Wrap uuid generator. Allows for testing with expected values."""
        return str(uuid4())
