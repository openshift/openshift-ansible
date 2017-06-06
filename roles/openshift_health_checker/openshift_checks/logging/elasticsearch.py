"""
Module for performing checks on an Elasticsearch logging deployment
"""

import json
import re

from openshift_checks import get_var
from openshift_checks.logging.logging import LoggingCheck


class Elasticsearch(LoggingCheck):
    """Module that checks an integrated logging Elasticsearch deployment"""

    name = "elasticsearch"
    tags = ["health", "logging"]

    logging_namespace = None

    def run(self, tmp, task_vars):
        """Check various things and gather errors. Returns: result as hash"""

        self.logging_namespace = get_var(task_vars, "openshift_logging_namespace", default="logging")
        es_pods, error = super(Elasticsearch, self).get_pods_for_component(
            self.execute_module,
            self.logging_namespace,
            "es",
            task_vars,
        )
        if error:
            return {"failed": True, "changed": False, "msg": error}
        check_error = self.check_elasticsearch(es_pods, task_vars)

        if check_error:
            msg = ("The following Elasticsearch deployment issue was found:"
                   "\n-------\n"
                   "{}".format(check_error))
            return {"failed": True, "changed": False, "msg": msg}

        # TODO(lmeyer): run it all again for the ops cluster
        return {"failed": False, "changed": False, "msg": 'No problems found with Elasticsearch deployment.'}

    def _not_running_elasticsearch_pods(self, es_pods):
        """Returns: list of running pods, list of errors about non-running pods"""
        not_running = super(Elasticsearch, self).not_running_pods(es_pods)
        if not_running:
            return not_running, [(
                'The following Elasticsearch pods are not running:\n'
                '{pods}'
                'These pods will not aggregate logs from their nodes.'
            ).format(pods=''.join(
                "  {} ({})\n".format(pod['metadata']['name'], pod['spec'].get('host', 'None'))
                for pod in not_running
            ))]
        return not_running, []

    def check_elasticsearch(self, es_pods, task_vars):
        """Various checks for elasticsearch. Returns: error string"""
        not_running_pods, error_msgs = self._not_running_elasticsearch_pods(es_pods)
        running_pods = [pod for pod in es_pods if pod not in not_running_pods]
        pods_by_name = {
            pod['metadata']['name']: pod for pod in running_pods
            # Filter out pods that are not members of a DC
            if pod['metadata'].get('labels', {}).get('deploymentconfig')
        }
        if not pods_by_name:
            return 'No logging Elasticsearch pods were found. Is logging deployed?'
        error_msgs += self._check_elasticsearch_masters(pods_by_name, task_vars)
        error_msgs += self._check_elasticsearch_node_list(pods_by_name, task_vars)
        error_msgs += self._check_es_cluster_health(pods_by_name, task_vars)
        error_msgs += self._check_elasticsearch_diskspace(pods_by_name, task_vars)
        return '\n'.join(error_msgs)

    @staticmethod
    def _build_es_curl_cmd(pod_name, url):
        base = "exec {name} -- curl -s --cert {base}cert --key {base}key --cacert {base}ca -XGET '{url}'"
        return base.format(base="/etc/elasticsearch/secret/admin-", name=pod_name, url=url)

    def _check_elasticsearch_masters(self, pods_by_name, task_vars):
        """Check that Elasticsearch masters are sane. Returns: list of error strings"""
        es_master_names = set()
        error_msgs = []
        for pod_name in pods_by_name.keys():
            # Compare what each ES node reports as master and compare for split brain
            get_master_cmd = self._build_es_curl_cmd(pod_name, "https://localhost:9200/_cat/master")
            master_name_str = self._exec_oc(get_master_cmd, [], task_vars)
            master_names = (master_name_str or '').split(' ')
            if len(master_names) > 1:
                es_master_names.add(master_names[1])
            else:
                error_msgs.append(
                    'No master? Elasticsearch {pod} returned bad string when asked master name:\n'
                    '  {response}'.format(pod=pod_name, response=master_name_str)
                )

        if not es_master_names:
            error_msgs.append('No logging Elasticsearch masters were found. Is logging deployed?')
            return '\n'.join(error_msgs)

        if len(es_master_names) > 1:
            error_msgs.append(
                'Found multiple Elasticsearch masters according to the pods:\n'
                '{master_list}\n'
                'This implies that the masters have "split brain" and are not correctly\n'
                'replicating data for the logging cluster. Log loss is likely to occur.'
                .format(master_list='\n'.join('  ' + master for master in es_master_names))
            )

        return error_msgs

    def _check_elasticsearch_node_list(self, pods_by_name, task_vars):
        """Check that reported ES masters are accounted for by pods. Returns: list of error strings"""

        if not pods_by_name:
            return ['No logging Elasticsearch masters were found. Is logging deployed?']

        # get ES cluster nodes
        node_cmd = self._build_es_curl_cmd(list(pods_by_name.keys())[0], 'https://localhost:9200/_nodes')
        cluster_node_data = self._exec_oc(node_cmd, [], task_vars)
        try:
            cluster_nodes = json.loads(cluster_node_data)['nodes']
        except (ValueError, KeyError):
            return [
                'Failed to query Elasticsearch for the list of ES nodes. The output was:\n' +
                cluster_node_data
            ]

        # Try to match all ES-reported node hosts to known pods.
        error_msgs = []
        for node in cluster_nodes.values():
            # Note that with 1.4/3.4 the pod IP may be used as the master name
            if not any(node['host'] in (pod_name, pod['status'].get('podIP'))
                       for pod_name, pod in pods_by_name.items()):
                error_msgs.append(
                    'The Elasticsearch cluster reports a member node "{node}"\n'
                    'that does not correspond to any known ES pod.'.format(node=node['host'])
                )

        return error_msgs

    def _check_es_cluster_health(self, pods_by_name, task_vars):
        """Exec into the elasticsearch pods and check the cluster health. Returns: list of errors"""
        error_msgs = []
        for pod_name in pods_by_name.keys():
            cluster_health_cmd = self._build_es_curl_cmd(pod_name, 'https://localhost:9200/_cluster/health?pretty=true')
            cluster_health_data = self._exec_oc(cluster_health_cmd, [], task_vars)
            try:
                health_res = json.loads(cluster_health_data)
                if not health_res or not health_res.get('status'):
                    raise ValueError()
            except ValueError:
                error_msgs.append(
                    'Could not retrieve cluster health status from logging ES pod "{pod}".\n'
                    'Response was:\n{output}'.format(pod=pod_name, output=cluster_health_data)
                )
                continue

            if health_res['status'] not in ['green', 'yellow']:
                error_msgs.append(
                    'Elasticsearch cluster health status is RED according to pod "{}"'.format(pod_name)
                )

        return error_msgs

    def _check_elasticsearch_diskspace(self, pods_by_name, task_vars):
        """
        Exec into an ES pod and query the diskspace on the persistent volume.
        Returns: list of errors
        """
        error_msgs = []
        for pod_name in pods_by_name.keys():
            df_cmd = 'exec {} -- df --output=ipcent,pcent /elasticsearch/persistent'.format(pod_name)
            disk_output = self._exec_oc(df_cmd, [], task_vars)
            lines = disk_output.splitlines()
            # expecting one header looking like 'IUse% Use%' and one body line
            body_re = r'\s*(\d+)%?\s+(\d+)%?\s*$'
            if len(lines) != 2 or len(lines[0].split()) != 2 or not re.match(body_re, lines[1]):
                error_msgs.append(
                    'Could not retrieve storage usage from logging ES pod "{pod}".\n'
                    'Response to `df` command was:\n{output}'.format(pod=pod_name, output=disk_output)
                )
                continue
            inode_pct, disk_pct = re.match(body_re, lines[1]).groups()

            inode_pct_thresh = get_var(task_vars, 'openshift_check_efk_es_inode_pct', default='90')
            if int(inode_pct) >= int(inode_pct_thresh):
                error_msgs.append(
                    'Inode percent usage on the storage volume for logging ES pod "{pod}"\n'
                    '  is {pct}, greater than threshold {limit}.\n'
                    '  Note: threshold can be specified in inventory with {param}'.format(
                        pod=pod_name,
                        pct=str(inode_pct),
                        limit=str(inode_pct_thresh),
                        param='openshift_check_efk_es_inode_pct',
                    ))
            disk_pct_thresh = get_var(task_vars, 'openshift_check_efk_es_storage_pct', default='80')
            if int(disk_pct) >= int(disk_pct_thresh):
                error_msgs.append(
                    'Disk percent usage on the storage volume for logging ES pod "{pod}"\n'
                    '  is {pct}, greater than threshold {limit}.\n'
                    '  Note: threshold can be specified in inventory with {param}'.format(
                        pod=pod_name,
                        pct=str(disk_pct),
                        limit=str(disk_pct_thresh),
                        param='openshift_check_efk_es_storage_pct',
                    ))

        return error_msgs

    def _exec_oc(self, cmd_str, extra_args, task_vars):
        return super(Elasticsearch, self).exec_oc(
            self.execute_module,
            self.logging_namespace,
            cmd_str,
            extra_args,
            task_vars,
        )
