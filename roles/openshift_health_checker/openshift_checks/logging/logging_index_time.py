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
        pod_log_timeout = int(get_var(task_vars, "openshift_check_pod_logs_timeout", default=ES_CMD_TIMEOUT_SECONDS))

        # get all Kibana pods
        self.logging_namespace = get_var(task_vars, "openshift_logging_namespace", default=self.logging_namespace)
        pods, error = super(LoggingIndexTime, self).get_pods_for_component(
            self.execute_module,
            self.logging_namespace,
            "kibana",
            task_vars,
        )

        if error:
            msg = 'Unable to retrieve pods for the "Kibanna" logging component: {}'
            return {"failed": True, "changed": False, "msg": msg.format(error)}

        running_kibana_pods = self.running_pods(pods)
        if not len(running_kibana_pods):
            msg = ('No Kibana pods were found to be in the "Running" state.'
                   'At least one Kibana pod is required in order to perform this check.')
            return {"failed": True, "changed": False, "msg": msg}

        # get all Elasticsearch pods
        pods, error = super(LoggingIndexTime, self).get_pods_for_component(
            self.execute_module,
            self.logging_namespace,
            "es",
            task_vars,
        )

        if error:
            msg = 'Unable to retrieve pods for the "Elasticsearch" logging component: {}'
            return {"failed": True, "changed": False, "msg": msg.format(error)}

        running_es_pods = self.running_pods(pods)
        if not len(running_es_pods):
            msg = ('No Elasticsearch pods were found to be in the "Running" state.'
                   'At least one Elasticsearch pod is required in order to perform this check.')
            return {"failed": True, "changed": False, "msg": msg}

        uuid = self.curl_kibana_with_uuid(running_kibana_pods[0], task_vars)
        self.wait_until_cmd_or_err(running_es_pods[0], uuid, pod_log_timeout, task_vars)
        return {}

    def wait_until_cmd_or_err(self, es_pod, uuid, timeout_secs, task_vars):
        """Wait a maximum of timeout_secs for the uuid logged in Kibana to be
        found in the Elasticsearch logs. Since we are querying for a message
        with the uuid that was set earlier, there should only be a single match.
        Raise an OpenShiftCheckException if timeout is reached finding a match."""
        now = int(time.time())
        time_start = now
        time_end = time_start + timeout_secs
        interval = 1  # seconds to wait between retries

        while now < time_end:
            if self.query_es_from_es(es_pod, uuid, task_vars):
                return

            time.sleep(interval)
            now = int(time.time())
            if now < time_start:  # saw a large clock reset: start the timer again
                time_start = now
                time_end = now + timeout_secs

        msg = "expecting match in Elasticsearch for message with uuid {}, but no matches were found after {}s."
        raise OpenShiftCheckException(msg.format(uuid, timeout_secs))

    def curl_kibana_with_uuid(self, kibanna_pod, task_vars):
        """curl Kibana with a unique uuid."""
        uuid = self.generate_uuid()
        pod_name = kibanna_pod["metadata"]["name"]
        exec_cmd = "exec {pod_name} -c kibana -- curl --max-time 30 -s http://localhost:5601/{uuid}"
        exec_cmd = exec_cmd.format(pod_name=pod_name, uuid=uuid)

        error_str = self.oc_cmd(exec_cmd, [], task_vars)

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
        result = self.oc_cmd(exec_cmd, [], task_vars)

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
        """Returns: list of pods in a running state"""
        return [
            pod for pod in pods
            if pod['status']['phase'] == 'Running'
        ]

    @staticmethod
    def generate_uuid():
        """Wrap uuid generator. Allows for testing with expected values."""
        return str(uuid4())

    def oc_cmd(self, cmd_str, extra_args, task_vars):
        """Wrap parent exec_oc method. Allows for testing without actually invoking other modules."""
        return super(LoggingIndexTime, self).exec_oc(
            self.execute_module,
            self.logging_namespace,
            cmd_str,
            extra_args,
            task_vars
        )
