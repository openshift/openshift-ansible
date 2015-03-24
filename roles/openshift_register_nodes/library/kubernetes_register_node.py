#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4

import os
import multiprocessing
import socket
from subprocess import check_output, Popen
from decimal import *

DOCUMENTATION = '''
---
module: kubernetes_register_node
short_description: Registers a kubernetes node with a master
description:
    - Registers a kubernetes node with a master
options:
    name:
        default: null
        description:
            - Identifier for this node (usually the node fqdn).
        required: true
    api_verison:
        choices: ['v1beta1', 'v1beta3']
        default: 'v1beta1'
        description:
            - Kubernetes API version to use
        required: true
    host_ip:
        default: null
        description:
            - IP Address to associate with the node when registering.
              Available in the following API versions: v1beta1.
        required: false
    hostnames:
        default: []
        description:
            - Valid hostnames for this node. Available in the following API
              versions: v1beta3.
        required: false
    external_ips:
        default: []
        description:
            - External IP Addresses for this node. Available in the following API
              versions: v1beta3.
        required: false
    internal_ips:
        default: []
        description:
            - Internal IP Addresses for this node. Available in the following API
              versions: v1beta3.
        required: false
    cpu:
        default: null
        description:
            - Number of CPUs to allocate for this node. When using the v1beta1
              API, you must specify the CPU count as a floating point number
              with no more than 3 decimal places. API version v1beta3 and newer
              accepts arbitrary float values.
        required: false
    memory:
        default: null
        description:
            - Memory available for this node. When using the v1beta1 API, you
              must specify the memory size in bytes. API version v1beta3 and
              newer accepts binary SI and decimal SI values.
        required: false
'''
EXAMPLES = '''
# Minimal node registration
- openshift_register_node: name=ose3.node.example.com

# Node registration using the v1beta1 API and assigning 1 CPU core and 10 GB of
# Memory
- openshift_register_node:
    name: ose3.node.example.com
    api_version: v1beta1
    hostIP: 192.168.1.1
    cpu: 1
    memory: 500000000

# Node registration using the v1beta3 API, setting an alternate hostname,
# internalIP, externalIP and assigning 3.5 CPU cores and 1 TiB of Memory
- openshift_register_node:
    name: ose3.node.example.com
    api_version: v1beta3
    external_ips: ['192.168.1.5']
    internal_ips: ['10.0.0.5']
    hostnames: ['ose2.node.internal.local']
    cpu: 3.5
    memory: 1Ti
'''


class ClientConfigException(Exception):
    pass

class ClientConfig:
    def __init__(self, client_opts, module):
        _, output, error = module.run_command(["/usr/bin/openshift", "ex",
                                               "config", "view", "-o",
                                               "json"] + client_opts,
                                              check_rc = True)
        self.config = json.loads(output)

        if not (bool(self.config['clusters']) or
                bool(self.config['contexts']) or
                bool(self.config['current-context']) or
                bool(self.config['users'])):
            raise ClientConfigException(msg="Client config missing required " \
                                            "values",
                                        output=output)

    def current_context(self):
        return self.config['current-context']

    def section_has_value(self, section_name, value):
        section = self.config[section_name]
        if isinstance(section, dict):
            return value in section
        else:
            val = next((item for item in section
                      if item['name'] == value), None)
            return val is not None

    def has_context(self, context):
        return self.section_has_value('contexts', context)

    def has_user(self, user):
        return self.section_has_value('users', user)

    def has_cluster(self, cluster):
        return self.section_has_value('clusters', cluster)

    def get_value_for_context(self, context, attribute):
        contexts = self.config['contexts']
        if isinstance(contexts, dict):
            return contexts[context][attribute]
        else:
            return next((c['context'][attribute] for c in contexts
                      if c['name'] == context), None)

    def get_user_for_context(self, context):
        return self.get_value_for_context(context, 'user')

    def get_cluster_for_context(self, context):
        return self.get_value_for_context(context, 'cluster')

class Util:
    @staticmethod
    def remove_empty_elements(mapping):
        if isinstance(mapping, dict):
            m = mapping.copy()
            for key, val in mapping.iteritems():
                if not val:
                    del m[key]
            return m
        else:
            return mapping

class NodeResources:
    def __init__(self, version, cpu=None, memory=None):
        if version == 'v1beta1':
            self.resources = dict(capacity=dict())
            self.resources['capacity']['cpu'] = cpu
            self.resources['capacity']['memory'] = memory

    def get_resources(self):
        return Util.remove_empty_elements(self.resources)

class NodeSpec:
    def __init__(self, version, cpu=None, memory=None, cidr=None, externalID=None):
        if version == 'v1beta3':
            self.spec = dict(podCIDR=cidr, externalID=externalID,
                             capacity=dict())
            self.spec['capacity']['cpu'] = cpu
            self.spec['capacity']['memory'] = memory

    def get_spec(self):
        return Util.remove_empty_elements(self.spec)

class NodeStatus:
    def addAddresses(self, addressType, addresses):
        addressList = []
        for address in addresses:
            addressList.append(dict(type=addressType, address=address))
        return addressList

    def __init__(self, version, externalIPs = [], internalIPs = [],
                 hostnames = []):
        if version == 'v1beta3':
            self.status = dict(addresses = addAddresses('ExternalIP',
                                                        externalIPs) +
                                           addAddresses('InternalIP',
                                                        internalIPs) +
                                           addAddresses('Hostname',
                                                        hostnames))

    def get_status(self):
        return Util.remove_empty_elements(self.status)

class Node:
    def __init__(self, module, client_opts, version='v1beta1', name=None,
                 hostIP = None, hostnames=[], externalIPs=[], internalIPs=[],
                 cpu=None, memory=None, labels=dict(), annotations=dict(),
                 podCIDR=None, externalID=None):
        self.module = module
        self.client_opts = client_opts
        if version == 'v1beta1':
            self.node = dict(id = name,
                             kind = 'Node',
                             apiVersion = version,
                             hostIP = hostIP,
                             resources = NodeResources(version, cpu, memory),
                             cidr = podCIDR,
                             labels = labels,
                             annotations = annotations
                        )
        elif version == 'v1beta3':
            metadata = dict(name = name,
                            labels = labels,
                            annotations = annotations
                        )
            self.node = dict(kind = 'Node',
                             apiVersion = version,
                             metadata = metadata,
                             spec = NodeSpec(version, cpu, memory, podCIDR,
                                             externalID),
                             status = NodeStatus(version, externalIPs,
                                                 internalIPs, hostnames),
                        )

    def get_name(self):
        if self.node['apiVersion'] == 'v1beta1':
            return self.node['id']
        elif self.node['apiVersion'] == 'v1beta3':
            return self.node['name']

    def get_node(self):
        node = self.node.copy()
        if self.node['apiVersion'] == 'v1beta1':
            node['resources'] = self.node['resources'].get_resources()
        elif self.node['apiVersion'] == 'v1beta3':
            node['spec'] = self.node['spec'].get_spec()
            node['status'] = self.node['status'].get_status()
        return Util.remove_empty_elements(node)

    def exists(self):
        _, output, error = self.module.run_command(["/usr/bin/osc", "get",
                                                    "nodes"] +  self.client_opts,
                                                   check_rc = True)
        if re.search(self.module.params['name'], output, re.MULTILINE):
            return True
        return False

    def create(self):
        cmd = ['/usr/bin/osc'] + self.client_opts + ['create', 'node', '-f', '-']
        rc, output, error = self.module.run_command(cmd,
                                               data=self.module.jsonify(self.get_node()))
        if rc != 0:
            if re.search("minion \"%s\" already exists" % self.get_name(),
                         error):
                self.module.exit_json(changed=False,
                                 msg="node definition already exists",
                                 node=self.get_node())
            else:
                self.module.fail_json(msg="Node creation failed.", rc=rc,
                                 output=output, error=error,
                                 node=self.get_node())
        else:
            return True

def main():
    module = AnsibleModule(
        argument_spec      = dict(
            name           = dict(required = True, type = 'str'),
            host_ip        = dict(type = 'str'),
            hostnames      = dict(type = 'list', default = []),
            external_ips   = dict(type = 'list', default = []),
            internal_ips   = dict(type = 'list', default = []),
            api_version    = dict(type = 'str', default = 'v1beta1', # TODO: after kube rebase, we can default to v1beta3
                                  choices = ['v1beta1', 'v1beta3']),
            cpu            = dict(type = 'str'),
            memory         = dict(type = 'str'),
            labels         = dict(type = 'dict', default = {}), # TODO: needs documented
            annotations    = dict(type = 'dict', default = {}), # TODO: needs documented
            pod_cidr       = dict(type = 'str'), # TODO: needs documented
            external_id    = dict(type = 'str'), # TODO: needs documented
            client_config  = dict(type = 'str'), # TODO: needs documented
            client_cluster = dict(type = 'str', default = 'master'), # TODO: needs documented
            client_context = dict(type = 'str', default = 'master'), # TODO: needs documented
            client_user    = dict(type = 'str', default = 'admin') # TODO: needs documented
        ),
        mutually_exclusive = [
            ['host_ip', 'external_ips'],
            ['host_ip', 'internal_ips'],
            ['host_ip', 'hostnames'],
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
        config = ClientConfig(client_opts, module)
    except ClientConfigException as e:
        module.fail_json(msg="Failed to get client configuration", exception=e)

    client_context = module.params['client_context']
    if config.has_context(client_context):
        if client_context != config.current_context():
            client_opts.append("--context=%s" % client_context)
    else:
        module.fail_json(msg="Context %s not found in client config" %
                         client_context)

    client_user = module.params['client_user']
    if config.has_user(client_user):
        if client_user != config.get_user_for_context(client_context):
            client_opts.append("--user=%s" % client_user)
    else:
        module.fail_json(msg="User %s not found in client config" %
                         client_user)

    client_cluster = module.params['client_cluster']
    if config.has_cluster(client_cluster):
        if client_cluster != config.get_cluster_for_context(client_cluster):
            client_opts.append("--cluster=%s" % client_cluster)
    else:
        module.fail_json(msg="Cluster %s not found in client config" %
                         client_cluster)

    # TODO: provide sane defaults for some (like hostname, externalIP,
    # internalIP, etc)
    node = Node(module, client_opts, module.params['api_version'],
                module.params['name'], module.params['host_ip'],
                module.params['hostnames'], module.params['external_ips'],
                module.params['internal_ips'], module.params['cpu'],
                module.params['memory'], module.params['labels'],
                module.params['annotations'], module.params['pod_cidr'],
                module.params['external_id'])

    # TODO: attempt to support changing node settings where possible and/or
    # modifying node resources
    if node.exists():
        module.exit_json(changed=False, node=node.get_node())
    elif module.check_mode:
        module.exit_json(changed=True, node=node.get_node())
    else:
        if node.create():
            module.exit_json(changed=True,
                             msg="Node created successfully",
                             node=node.get_node())
        else:
            module.fail_json(msg="Unknown error creating node",
                             node=node.get_node())


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
