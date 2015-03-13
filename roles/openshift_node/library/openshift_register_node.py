#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4

import os
import multiprocessing
import socket
from subprocess import check_output, Popen

DOCUMENTATION = '''
---
module: openshift_register_node
short_description: This module registers an openshift-node with an openshift-master
author: Jason DeTiberus
requirements: [ openshift-node ]
notes: Node resources can be specified using either the resources option or the following options: cpu, memory
options:
    name:
        description:
            - id for this node (usually the node fqdn)
        required: true
    hostIP:
        description:
            - ip address for this node
        required: false
    cpu:
        description:
            - number of CPUs for this node
        required: false
        default: number of logical CPUs detected
    memory:
        description:
            - Memory available for this node in bytes
        required: false
        default: 80% MemTotal
    resources:
        description:
            - A json string representing Node resources
        required: false
'''
EXAMPLES = '''
# Minimal node registration
- openshift_register_node: name=ose3.node.example.com

# Node registration with all options (using cpu and memory options)
- openshift_register_node:
    name: ose3.node.example.com
    hostIP: 192.168.1.1
    apiVersion: v1beta1
    cpu: 1
    memory: 1073741824

# Node registration with all options (using resources option)
- openshift_register_node:
    name: ose3.node.example.com
    hostIP: 192.168.1.1
    apiVersion: v1beta1
    resources:
        capacity:
            cpu: 1
            memory: 1073741824
'''

def main():
    module = AnsibleModule(
        argument_spec      = dict(
            name           = dict(required = True),
            hostIP         = dict(),
            apiVersion     = dict(),
            cpu            = dict(),
            memory         = dict(),
            resources      = dict(),
            client_config  = dict(),
            client_cluster = dict(default = 'master'),
            client_context = dict(default = 'master'),
            client_user    = dict(default = 'admin')
        ),
        mutually_exclusive = [
            ['resources', 'cpu'],
            ['resources', 'memory']
        ],
        supports_check_mode=True
    )

    user_has_client_config = os.path.exists(os.path.expanduser('~/.kube/.kubeconfig'))
    if not (user_has_client_config or module.params['client_config']):
        module.fail_json(msg="Could not locate client configuration, "
                         "client_config must be specified if "
                         "~/.kube/.kubeconfig is not present")

    client_opts = []
    if module.params['client_config']:
        client_opts.append("--kubeconfig=%s" % module.params['client_config'])

    try:
        output = check_output(["/usr/bin/openshift", "ex", "config", "view",
                               "-o", "json"] + client_opts,
                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        module.fail_json(msg="Failed to get client configuration",
                command=e.cmd, returncode=e.returncode, output=e.output)

    config = json.loads(output)
    if not (bool(config['clusters']) or bool(config['contexts']) or
            bool(config['current-context']) or bool(config['users'])):
        module.fail_json(msg="Client config missing required values",
                         output=output)

    client_context = module.params['client_context']
    if client_context:
        config_context = next((context for context in config['contexts']
                               if context['name'] == client_context), None)
        if not config_context:
            module.fail_json(msg="Context %s not found in client config" %
                             client_context)
        if not config['current-context'] or config['current-context'] != client_context:
            client_opts.append("--context=%s" % client_context)

    client_user = module.params['client_user']
    if client_user:
        config_user = next((user for user in config['users']
                            if user['name'] == client_user), None)
        if not config_user:
            module.fail_json(msg="User %s not found in client config" %
                             client_user)
        if client_user != config_context['context']['user']:
            client_opts.append("--user=%s" % client_user)

    client_cluster = module.params['client_cluster']
    if client_cluster:
        config_cluster = next((cluster for cluster in config['clusters']
                               if cluster['name'] == client_cluster), None)
        if not client_cluster:
            module.fail_json(msg="Cluster %s not found in client config" %
                             client_cluster)
        if client_cluster != config_context['context']['cluster']:
            client_opts.append("--cluster=%s" % client_cluster)

    node_def = dict(
            id = module.params['name'],
            kind = 'Node',
            apiVersion = 'v1beta1',
            resources = dict(
                capacity = dict()
            )
    )

    for key, value in module.params.iteritems():
        if key in ['cpu', 'memory']:
            node_def['resources']['capacity'][key] = value
        elif key == 'name':
            node_def['id'] = value
        elif key != 'client_config':
            if value:
                node_def[key] = value

    if not node_def['resources']['capacity']['cpu']:
        node_def['resources']['capacity']['cpu'] = multiprocessing.cpu_count()

    if not node_def['resources']['capacity']['memory']:
        with open('/proc/meminfo', 'r') as mem:
            for line in mem:
                entries = line.split()
                if str(entries.pop(0)) == 'MemTotal:':
                    mem_total_kb = int(entries.pop(0))
                    mem_capacity = int(mem_total_kb * 1024 * .75)
                    node_def['resources']['capacity']['memory'] = mem_capacity
                    break

    try:
        output = check_output(["/usr/bin/osc", "get", "nodes"] +  client_opts,
                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        module.fail_json(msg="Failed to get node list", command=e.cmd,
                returncode=e.returncode, output=e.output)

    if re.search(module.params['name'], output, re.MULTILINE):
        module.exit_json(changed=False, node_def=node_def)
    elif module.check_mode:
        module.exit_json(changed=True, node_def=node_def)

    config_def = dict(
        metadata = dict(
            name = "add-node-%s" % module.params['name']
        ),
        kind = 'Config',
        apiVersion = 'v1beta1',
        items = [node_def]
    )

    p = Popen(["/usr/bin/osc"] + client_opts + ["create", "node"] + ["-f", "-"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, close_fds=True)
    (out, err) = p.communicate(module.jsonify(config_def))
    ret = p.returncode

    if ret != 0:
        if re.search("minion \"%s\" already exists" % module.params['name'],
                err):
            module.exit_json(changed=False,
                    msg="node definition already exists", config_def=config_def)
        else:
            module.fail_json(msg="Node creation failed.", ret=ret, out=out,
                    err=err, config_def=config_def)

    module.exit_json(changed=True, out=out, err=err, ret=ret,
           node_def=config_def)

# import module snippets
from ansible.module_utils.basic import *
main()
