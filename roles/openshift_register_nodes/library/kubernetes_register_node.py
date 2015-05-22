#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4
#
# disable pylint checks
# permanently disabled unless someone wants to refactor the object model:
#   too-few-public-methods
#   no-self-use
#   too-many-arguments
#   too-many-locals
#   too-many-branches
# pylint:disable=too-many-arguments, no-self-use
# pylint:disable=too-many-locals, too-many-branches, too-few-public-methods
"""Ansible module to register a kubernetes node to the cluster"""

import os

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
'''


class ClientConfigException(Exception):
    """Client Configuration Exception"""
    pass

class ClientConfig(object):
    """ Representation of a client config

        Attributes:
            config (dict): dictionary representing the client configuration

        Args:
            client_opts (list of str): client options to use
            module (AnsibleModule):

        Raises:
            ClientConfigException:
    """
    def __init__(self, client_opts, module):
        kubectl = module.params['kubectl_cmd']
        _, output, _ = module.run_command((kubectl +
                                           ["config", "view", "-o", "json"] +
                                           client_opts), check_rc=True)
        self.config = json.loads(output)

        if not (bool(self.config['clusters']) or
                bool(self.config['contexts']) or
                bool(self.config['current-context']) or
                bool(self.config['users'])):
            raise ClientConfigException(
                "Client config missing required values: %s" % output
            )

    def current_context(self):
        """ Gets the current context for the client config

            Returns:
                str: The current context as set in the config
        """
        return self.config['current-context']

    def section_has_value(self, section_name, value):
        """ Test if specified section contains a value

            Args:
                section_name (str): config section to test
                value (str): value to test if present
            Returns:
                bool: True if successful, false otherwise
        """
        section = self.config[section_name]
        if isinstance(section, dict):
            return value in section
        else:
            val = next((item for item in section
                        if item['name'] == value), None)
            return val is not None

    def has_context(self, context):
        """ Test if specified context exists in config

            Args:
                context (str): value to test if present
            Returns:
                bool: True if successful, false otherwise
        """
        return self.section_has_value('contexts', context)

    def has_user(self, user):
        """ Test if specified user exists in config

            Args:
                context (str): value to test if present
            Returns:
                bool: True if successful, false otherwise
        """
        return self.section_has_value('users', user)

    def has_cluster(self, cluster):
        """ Test if specified cluster exists in config

            Args:
                context (str): value to test if present
            Returns:
                bool: True if successful, false otherwise
        """
        return self.section_has_value('clusters', cluster)

    def get_value_for_context(self, context, attribute):
        """ Get the value of attribute in context

            Args:
                context (str): context to search
                attribute (str): attribute wanted
            Returns:
                str: The value for attribute in context
        """
        contexts = self.config['contexts']
        if isinstance(contexts, dict):
            return contexts[context][attribute]
        else:
            return next((c['context'][attribute] for c in contexts
                         if c['name'] == context), None)

    def get_user_for_context(self, context):
        """ Get the user attribute in context

            Args:
                context (str): context to search
            Returns:
                str: The value for the attribute in context
        """
        return self.get_value_for_context(context, 'user')

    def get_cluster_for_context(self, context):
        """ Get the cluster attribute in context

            Args:
                context (str): context to search
            Returns:
                str: The value for the attribute in context
        """
        return self.get_value_for_context(context, 'cluster')

    def get_namespace_for_context(self, context):
        """ Get the namespace attribute in context

            Args:
                context (str): context to search
            Returns:
                str: The value for the attribute in context
        """
        return self.get_value_for_context(context, 'namespace')

class Util(object):
    """Utility methods"""
    @staticmethod
    def remove_empty_elements(mapping):
        """ Recursively removes empty elements from a dict

            Args:
                mapping (dict): dict to remove empty attributes from
            Returns:
                dict: A copy of the dict with empty elements removed
        """
        if isinstance(mapping, dict):
            copy = mapping.copy()
            for key, val in mapping.iteritems():
                if not val:
                    del copy[key]
            return copy
        else:
            return mapping

class NodeResources(object):
    """ Kubernetes Node Resources

        Attributes:
            resources (dict): A dictionary representing the node resources

        Args:
            version (str): kubernetes api version
            cpu (str): string representation of the cpu resources for the node
            memory (str): string representation of the memory resources for the
                node
    """
    def __init__(self, version, cpu=None, memory=None):
        if version == 'v1beta1':
            self.resources = dict(capacity=dict())
            self.resources['capacity']['cpu'] = cpu
            self.resources['capacity']['memory'] = memory

    def get_resources(self):
        """ Get the dict representing the node resources

            Returns:
                dict: representation of the node resources with any empty
                    elements removed
        """
        return Util.remove_empty_elements(self.resources)

class NodeSpec(object):
    """ Kubernetes Node Spec

        Attributes:
            spec (dict): A dictionary representing the node resources

        Args:
            version (str): kubernetes api version
            cpu (str): string representation of the cpu resources for the node
            memory (str): string representation of the memory resources for the
                node
            cidr (str): string representation of the cidr block available for
                the node
            externalID (str): The external id of the node
    """
    def __init__(self, version, cpu=None, memory=None, cidr=None,
                 externalID=None):
        if version == 'v1beta3':
            self.spec = dict(podCIDR=cidr, externalID=externalID,
                             capacity=dict())
            self.spec['capacity']['cpu'] = cpu
            self.spec['capacity']['memory'] = memory

    def get_spec(self):
        """ Get the dict representing the node spec

            Returns:
                dict: representation of the node spec with any empty elements
                    removed
        """
        return Util.remove_empty_elements(self.spec)

class Node(object):
    """ Kubernetes Node

        Attributes:
            node (dict): A dictionary representing the node

        Args:
            module (AnsibleModule):
            client_opts (list): client connection options
            version (str, optional): kubernetes api version
            node_name (str, optional): name for node
            hostIP (str, optional): node host ip
            cpu (str, optional): cpu resources for the node
            memory (str, optional): memory resources for the node
            labels (list, optional): labels for the node
            annotations (list, optional): annotations for the node
            podCIDR (list, optional): cidr block to use for pods
            externalID (str, optional): external id of the node
    """
    def __init__(self, module, client_opts, version='v1beta1', node_name=None,
                 hostIP=None, cpu=None, memory=None, labels=None,
                 annotations=None, podCIDR=None, externalID=None):
        self.module = module
        self.client_opts = client_opts
        if version == 'v1beta1':
            self.node = dict(id=node_name,
                             kind='Node',
                             apiVersion=version,
                             hostIP=hostIP,
                             resources=NodeResources(version, cpu, memory),
                             cidr=podCIDR,
                             labels=labels,
                             annotations=annotations,
                             externalID=externalID)
        elif version == 'v1beta3':
            metadata = dict(name=node_name,
                            labels=labels,
                            annotations=annotations)
            self.node = dict(kind='Node',
                             apiVersion=version,
                             metadata=metadata,
                             spec=NodeSpec(version, cpu, memory, podCIDR,
                                           externalID))

    def get_name(self):
        """ Get the name for the node

            Returns:
                str: node name
        """
        if self.node['apiVersion'] == 'v1beta1':
            return self.node['id']
        elif self.node['apiVersion'] == 'v1beta3':
            return self.node['name']

    def get_node(self):
        """ Get the dict representing the node

            Returns:
                dict: representation of the node with any empty elements
                    removed
        """
        node = self.node.copy()
        if self.node['apiVersion'] == 'v1beta1':
            node['resources'] = self.node['resources'].get_resources()
        elif self.node['apiVersion'] == 'v1beta3':
            node['spec'] = self.node['spec'].get_spec()
        return Util.remove_empty_elements(node)

    def exists(self):
        """ Tests if the node already exists

            Returns:
                bool: True if node exists, otherwise False
        """
        kubectl = self.module.params['kubectl_cmd']
        _, output, _ = self.module.run_command((kubectl + ["get", "nodes"] +
                                                self.client_opts),
                                               check_rc=True)
        if re.search(self.module.params['name'], output, re.MULTILINE):
            return True
        return False

    def create(self):
        """ Creates the node

            Returns:
                bool: True if node creation successful
        """
        kubectl = self.module.params['kubectl_cmd']
        cmd = kubectl + self.client_opts + ['create', '-f', '-']
        exit_code, output, error = self.module.run_command(
            cmd, data=self.module.jsonify(self.get_node())
        )
        if exit_code != 0:
            if re.search("minion \"%s\" already exists" % self.get_name(),
                         error):
                self.module.exit_json(msg="node definition already exists",
                                      changed=False, node=self.get_node())
            else:
                self.module.fail_json(msg="Node creation failed.",
                                      exit_code=exit_code,
                                      output=output, error=error,
                                      node=self.get_node())
        else:
            return True

def generate_client_opts(module):
    """ Generates the client options

        Args:
            module(AnsibleModule)

        Returns:
            str: client options
    """
    client_config = '~/.kube/.kubeconfig'
    if 'default_client_config' in module.params:
        client_config = module.params['default_client_config']
    user_has_client_config = os.path.exists(os.path.expanduser(client_config))
    if not (user_has_client_config or module.params['client_config']):
        module.fail_json(msg="Could not locate client configuration, "
                         "client_config must be specified if "
                         "~/.kube/.kubeconfig is not present")

    client_opts = []
    if module.params['client_config']:
        kubeconfig_flag = '--kubeconfig'
        if 'kubeconfig_flag' in module.params:
            kubeconfig_flag = module.params['kubeconfig_flag']
        client_opts.append(kubeconfig_flag + '=' + os.path.expanduser(module.params['client_config']))

    try:
        config = ClientConfig(client_opts, module)
    except ClientConfigException as ex:
        module.fail_json(msg="Failed to get client configuration",
                         exception=str(ex))

    client_context = module.params['client_context']
    if config.has_context(client_context):
        if client_context != config.current_context():
            client_opts.append("--context=%s" % client_context)
    else:
        module.fail_json(msg="Context %s not found in client config" % client_context)

    client_user = module.params['client_user']
    if config.has_user(client_user):
        if client_user != config.get_user_for_context(client_context):
            client_opts.append("--user=%s" % client_user)
    else:
        module.fail_json(msg="User %s not found in client config" % client_user)

    client_cluster = module.params['client_cluster']
    if config.has_cluster(client_cluster):
        if client_cluster != config.get_cluster_for_context(client_context):
            client_opts.append("--cluster=%s" % client_cluster)
    else:
        module.fail_json(msg="Cluster %s not found in client config" % client_cluster)

    client_namespace = module.params['client_namespace']
    if client_namespace != config.get_namespace_for_context(client_context):
        client_opts.append("--namespace=%s" % client_namespace)

    return client_opts


def main():
    """ main """
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True, type='str'),
            host_ip=dict(type='str'),
            api_version=dict(type='str', default='v1beta1',
                             choices=['v1beta1', 'v1beta3']),
            cpu=dict(type='str'),
            memory=dict(type='str'),
            # TODO: needs documented
            labels=dict(type='dict', default={}),
            # TODO: needs documented
            annotations=dict(type='dict', default={}),
            # TODO: needs documented
            pod_cidr=dict(type='str'),
            # TODO: needs documented
            client_config=dict(type='str'),
            # TODO: needs documented
            client_cluster=dict(type='str', default='master'),
            # TODO: needs documented
            client_context=dict(type='str', default='default'),
            # TODO: needs documented
            client_namespace=dict(type='str', default='default'),
            # TODO: needs documented
            client_user=dict(type='str', default='system:admin'),
            # TODO: needs documented
            kubectl_cmd=dict(type='list', default=['kubectl']),
            # TODO: needs documented
            kubeconfig_flag=dict(type='str'),
            # TODO: needs documented
            default_client_config=dict(type='str')
        ),
        supports_check_mode=True
    )

    labels = module.params['labels']
    kube_hostname_label = 'kubernetes.io/hostname'
    if kube_hostname_label not in labels:
        labels[kube_hostname_label] = module.params['name']

    node = Node(module, generate_client_opts(module),
                module.params['api_version'], module.params['name'],
                module.params['host_ip'], module.params['cpu'],
                module.params['memory'], labels, module.params['annotations'],
                module.params['pod_cidr'])

    if node.exists():
        module.exit_json(changed=False, node=node.get_node())
    elif module.check_mode:
        module.exit_json(changed=True, node=node.get_node())
    elif node.create():
        module.exit_json(changed=True, msg="Node created successfully",
                         node=node.get_node())
    else:
        module.fail_json(msg="Unknown error creating node", node=node.get_node())

# ignore pylint errors related to the module_utils import
# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import
# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
