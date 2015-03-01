#!/usr/bin/python
# -*- coding: utf-8 -*-

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
    default_config='/var/lib/openshift/openshift.local.certificates/admin/.kubeconfig'

    module = AnsibleModule(
        argument_spec     = dict(
            name          = dict(required = True),
            hostIP        = dict(),
            apiVersion    = dict(),
            cpu           = dict(),
            memory        = dict(),
            resources     = dict(),
            client_config = dict(default = default_config)
        ),
        supports_check_mode=True
    )

    if module.params['resources'] and (module.params['cpu'] or module.params['memory']):
        module.fail_json(msg="Error: argument resources cannot be specified with the following arguments: cpu, memory")

    client_env = os.environ.copy()
    client_env['KUBECONFIG'] = module.params['client_config']

    node_def = dict(
        metadata = dict(
            name = module.params['name']
        ),
        kind = 'Node',
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
                    mem_free_kb = int(entries.pop(0))
                    mem_capacity = int(mem_free_kb * 1024 * .80)
                    node_def['resources']['capacity']['memory'] = mem_capacity
                    break

    try:
        output = check_output("osc get nodes", shell=True, env=client_env,
                stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError as e:
        module.fail_json(msg="Failed to get node list", command=e.cmd,
                returncode=e.returncode, output=e.output)

    if module.check_mode:
        if re.search(module.params['name'], output, re.MULTILINE):
            module.exit_json(changed=False, node_def=node_def)
        else:
            module.exit_json(changed=True, node_def=node_def)

    p = Popen("osc create node -f -", shell=True, stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, close_fds=True,
            env=client_env)
    (out, err) = p.communicate(module.jsonify(node_def))
    ret = p.returncode

    if ret != 0:
        if re.search("minion \"%s\" already exists" % module.params['name'],
                err):
            module.exit_json(changed=False,
                    msg="node definition already exists", node_def=node_def)
        else:
            module.fail_json(msg="Node creation failed.", ret=ret, out=out,
                    err=err, node_def=node_def)

    module.exit_json(changed=True, out=out, err=err, ret=ret,
           node_def=node_def)

# import module snippets
from ansible.module_utils.basic import *
main()
