#!/usr/bin/env python
"""glusterfs_check_containerized module"""
# Copyright 2018 Red Hat, Inc. and/or its affiliates
# and other contributors as indicated by the @author tags.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess

from ansible.module_utils.basic import AnsibleModule


DOCUMENTATION = '''
---
module: glusterfs_check_containerized

short_description: Check health of each volume in glusterfs on openshift.

version_added: "2.6"

description:
    - This module attempts to ensure all volumes are in healthy state
      in a glusterfs cluster.  The module is meant to be failure-prone, retries
      should be executed at the ansible level, they are not implemented in
      this module.
      This module by executing the following (roughly):
      oc exec --namespace=<namespace> <podname> -- gluster volume list
      for volume in <volume list>:
        gluster volume heal <volume> info

author:
    - "Michael Gugino <mgugino@redhat.com>"
'''

EXAMPLES = '''
- name: glusterfs volumes check
  glusterfs_check_containerized
    oc_bin: "/usr/bin/oc"
    oc_conf: "/etc/origin/master/admin.kubeconfig"
    oc_namespace: "glusterfs"
    cluster_name: "glusterfs"
'''


def fail(module, err):
    """Fail on error"""
    result = {'failed': True,
              'changed': False,
              'msg': err,
              'state': 'unknown'}
    module.fail_json(**result)


def call_or_fail(module, call_args):
    """Call subprocess.check_output and return utf-8 decoded stdout or fail"""
    try:
        # Must decode as utf-8 for python3 compatibility
        res = subprocess.check_output(call_args).decode('utf-8')
    except subprocess.CalledProcessError as err:
        fail(module, str(err))
    return res


def get_valid_nodes(module, oc_exec, exclude_node):
    """Return a list of nodes that will be used to filter running pods"""
    call_args = oc_exec + ['get', 'nodes']
    res = call_or_fail(module, call_args)
    valid_nodes = []
    for line in res.split('\n'):
        fields = line.split()
        if not fields:
            continue
        if fields[0] != exclude_node and "Ready" in fields[1].split(','):
            valid_nodes.append(fields[0])
    if not valid_nodes:
        fail(module,
             'Unable to find suitable node in get nodes output: {}'.format(res))
    return valid_nodes


def select_pods(module, pods, target_nodes):
    """Select pods to attempt to run gluster commands on"""
    pod_names = []
    if target_nodes:
        for target_node in target_nodes:
            for pod in pods:
                if target_node in pod[6]:
                    pod_names.append(pod[0])
            if not pod_names:
                fail(module, 'no pod found on node {}'.format(target_node))
    else:
        pod_names.append(pods[0][0])

    return pod_names


def get_pods(module, oc_exec, cluster_name, valid_nodes):
    """Get all cluster pods"""
    call_args = oc_exec + ['get', 'pods', '-owide']
    res = call_or_fail(module, call_args)
    # res is returned as a tab/space-separated list with headers.
    res_lines = res.split('\n')
    pods = []
    name_search = 'glusterfs-{}'.format(cluster_name)
    res_lines = list(filter(None, res.split('\n')))

    for line in res_lines[1:]:
        fields = line.split()
        if not fields:
            continue
        if name_search in fields[0]:
            if fields[2] == "Running" and fields[6] in valid_nodes:
                pods.append(fields)

    if not pods:
        fail(module,
             "Unable to find pods: {}".format(res))
    else:
        return pods


def get_volume_list(module, oc_exec, pod_name):
    """Retrieve list of active volumes from gluster cluster"""
    call_args = oc_exec + ['exec', pod_name, '--', 'gluster', 'volume', 'list']
    res = call_or_fail(module, call_args)
    # This should always at least return heketidbstorage, so no need to check
    # for empty string.
    return list(filter(None, res.split('\n')))


def check_volume_health_info(module, oc_exec, pod_name, volume):
    """Check health info of gluster volume"""
    call_args = oc_exec + ['exec', pod_name, '--', 'gluster', 'volume', 'heal',
                           volume, 'info']
    res = call_or_fail(module, call_args)
    # Output is not easily parsed
    for line in res.split('\n'):
        if line.startswith('Number of entries:'):
            cols = line.split(':')
            if cols[1].strip() != '0':
                fail(module, 'volume {} is not ready'.format(volume))


def check_volumes(module, oc_exec, pod_names):
    """Check status of all volumes on cluster"""
    for pod_name in pod_names:
        volume_list = get_volume_list(module, oc_exec, pod_name)
        for volume in volume_list:
            check_volume_health_info(module, oc_exec, pod_name, volume)


def check_bricks_usage(module, oc_exec, pods):
    """Checks usage of all bricks in cluster"""
    full_bricks = {}
    failed = False
    for pod in pods:
        full_bricks[pod[6]] = []
        call_args = oc_exec + ['exec', pod[0], '--', 'df', '-kh']
        res = call_or_fail(module, call_args)
        for line in res.split('\n'):
            # Look for heketi-provisioned filesystems
            if '/var/lib/heketi' in line:
                cols = line.split()
                usage = int(cols[4].strip('%'))
                # If a brick's disk usage is greater than 96%, fail
                if usage > 96:
                    full_bricks[pod[6]].append(cols[5])
                    failed = True

    if failed:
        fail(module, 'bricks near capacity found: {}'.format(full_bricks))


def run_module():
    '''Run this module'''
    module_args = dict(
        oc_bin=dict(type='path', required=True),
        oc_conf=dict(type='path', required=True),
        oc_namespace=dict(type='str', required=True),
        cluster_name=dict(type='str', required=True),
        exclude_node=dict(type='str', required=True),
        target_nodes=dict(type='list', required=False),
        check_bricks=dict(type='bool', required=False, default=False),
    )
    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=module_args
    )
    oc_bin = module.params['oc_bin']
    oc_conf = '--config={}'.format(module.params['oc_conf'])
    oc_namespace = '--namespace={}'.format(module.params['oc_namespace'])
    cluster_name = module.params['cluster_name']
    exclude_node = module.params['exclude_node']
    target_nodes = module.params['target_nodes']
    check_bricks = module.params['check_bricks']

    oc_exec = [oc_bin, oc_conf, oc_namespace]

    # create a nodes to find a pod on; We don't want to try to execute on a
    # pod running on a "NotReady" node or the inventory_hostname node because
    # the pods might not actually be alive.
    valid_nodes = get_valid_nodes(module, [oc_bin, oc_conf], exclude_node)

    # Need to find alive pods to run gluster commands in.
    pods = get_pods(module, oc_exec, cluster_name, valid_nodes)
    pod_names = select_pods(module, pods, target_nodes)

    check_volumes(module, oc_exec, pod_names)

    if check_bricks:
        check_bricks_usage(module, oc_exec, pods)

    result = {'changed': False}
    module.exit_json(**result)


def main():
    """main"""
    run_module()


if __name__ == '__main__':
    main()
