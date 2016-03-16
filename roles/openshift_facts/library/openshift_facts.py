#!/usr/bin/python
# pylint: disable=too-many-lines
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4
# Reason: Disable pylint too-many-lines because we don't want to split up this file.
# Status: Permanently disabled to keep this module as self-contained as possible.

"""Ansible module for retrieving and setting openshift related facts"""

DOCUMENTATION = '''
---
module: openshift_facts
short_description: Cluster Facts
author: Jason DeTiberus
requirements: [ ]
'''
EXAMPLES = '''
'''

import ConfigParser
import copy
import os
import StringIO
import yaml
from distutils.util import strtobool
from distutils.version import LooseVersion
import struct
import socket
from dbus import SystemBus, Interface
from dbus.exceptions import DBusException


ORIGIN_DT_VALUES = {
    'service_type': 'atomic-openshift',
    'config_base': '/etc/origin',
    'data_dir': '/var/lib/origin',
    'master_image': 'openshift/origin',
    'cli_image': 'openshift/origin',
    'node_image': 'openshift/node',
    'ovs_image': 'openshift/openvswitch',
    'etcd_image': 'registry.access.redhat.com/rhel7/etcd'
}

ENT_BASE_DT_VALUES = {
    'service_type': 'atomic-openshift',
    'config_base': ORIGIN_DT_VALUES['config_base'],
    'data_dir': ORIGIN_DT_VALUES['data_dir'],
    'etcd_image': 'registry.access.redhat.com/rhel7/etcd'
}

AP_BETA_DT_VALUES = {
    'service_type': ENT_BASE_DT_VALUES['config_base'],
    'config_base': ENT_BASE_DT_VALUES['config_base'],
    'data_dir': ENT_BASE_DT_VALUES['data_dir'],
    'etcd_image': ENT_BASE_DT_VALUES['etcd_image'],
    'master_image': 'aep3_beta/aep',
    'cli_image': 'aep3_beta/aep',
    'node_image': 'aep3_beta/node',
    'ovs_image': 'aep3_beta/openvswitch',
}

AP_DT_VALUES = {
    'service_type': ENT_BASE_DT_VALUES['config_base'],
    'config_base': ENT_BASE_DT_VALUES['config_base'],
    'data_dir': ENT_BASE_DT_VALUES['data_dir'],
    'etcd_image': ENT_BASE_DT_VALUES['etcd_image'],
    'master_image': 'aep3/aep',
    'cli_image': 'aep3/aep',
    'node_image': 'aep3/node',
    'ovs_image': 'aep3/openvswitch',
}

OSE_DT_VALUES = {
    'service_type': ENT_BASE_DT_VALUES['config_base'],
    'config_base': ENT_BASE_DT_VALUES['config_base'],
    'data_dir': ENT_BASE_DT_VALUES['data_dir'],
    'etcd_image': ENT_BASE_DT_VALUES['etcd_image'],
    'master_image': 'openshift3/ose',
    'cli_image': 'openshift3/ose',
    'node_image': 'openshift3/node',
    'ovs_image': 'openshift3/openvswitch',
}

ONLINE_DT_VALUES = OSE_DT_VALUES

LEGACY_ENT_DT_VALUES = {
    'service_type': 'openshift',
    'config_base': '/etc/openshift',
    'data_dir': '/var/lib/openshift'
}

DEPLOYMENT_TYPE_VALUES = {
    'origin': ORIGIN_DT_VALUES,
    'enterprise': LEGACY_ENT_DT_VALUES,
    'openshift-enterprise': OSE_DT_VALUES,
    'atomic-enterprise': AP_DT_VALUES,
    'atomic-enterprise-beta': AP_BETA_DT_VALUES,
    'online': ONLINE_DT_VALUES
}


def migrate_docker_facts(facts):
    """ Apply migrations for docker facts """
    params = {
        'common': (
            'additional_registries',
            'insecure_registries',
            'blocked_registries',
            'options'
        ),
        'node': (
            'log_driver',
            'log_options'
        )
    }
    if 'docker' not in facts:
        facts['docker'] = {}
    for role in params.keys():
        if role in facts:
            for param in params[role]:
                old_param = 'docker_' + param
                if old_param in facts[role]:
                    facts['docker'][param] = facts[role].pop(old_param)
    return facts

def migrate_local_facts(facts):
    """ Apply migrations of local facts """
    migrated_facts = copy.deepcopy(facts)
    return migrate_docker_facts(migrated_facts)

def first_ip(network):
    """ Return the first IPv4 address in network

        Args:
            network (str): network in CIDR format
        Returns:
            str: first IPv4 address
    """
    atoi = lambda addr: struct.unpack("!I", socket.inet_aton(addr))[0]
    itoa = lambda addr: socket.inet_ntoa(struct.pack("!I", addr))

    (address, netmask) = network.split('/')
    netmask_i = (0xffffffff << (32 - atoi(netmask))) & 0xffffffff
    return itoa((atoi(address) & netmask_i) + 1)

def hostname_valid(hostname):
    """ Test if specified hostname should be considered valid

        Args:
            hostname (str): hostname to test
        Returns:
            bool: True if valid, otherwise False
    """
    if (not hostname or
            hostname.startswith('localhost') or
            hostname.endswith('localdomain') or
            len(hostname.split('.')) < 2):
        return False

    return True


def choose_hostname(hostnames=None, fallback=''):
    """ Choose a hostname from the provided hostnames

        Given a list of hostnames and a fallback value, choose a hostname to
        use. This function will prefer fqdns if they exist (excluding any that
        begin with localhost or end with localdomain) over ip addresses.

        Args:
            hostnames (list): list of hostnames
            fallback (str): default value to set if hostnames does not contain
                            a valid hostname
        Returns:
            str: chosen hostname
    """
    hostname = fallback
    if hostnames is None:
        return hostname

    ip_regex = r'\A\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\Z'
    ips = [i for i in hostnames
           if (i is not None and isinstance(i, basestring)
               and re.match(ip_regex, i))]
    hosts = [i for i in hostnames
             if i is not None and i != '' and i not in ips]

    for host_list in (hosts, ips):
        for host in host_list:
            if hostname_valid(host):
                return host

    return hostname


def query_metadata(metadata_url, headers=None, expect_json=False):
    """ Return metadata from the provided metadata_url

        Args:
            metadata_url (str): metadata url
            headers (dict): headers to set for metadata request
            expect_json (bool): does the metadata_url return json
        Returns:
            dict or list: metadata request result
    """
    result, info = fetch_url(module, metadata_url, headers=headers)
    if info['status'] != 200:
        raise OpenShiftFactsMetadataUnavailableError("Metadata unavailable")
    if expect_json:
        return module.from_json(result.read())
    else:
        return [line.strip() for line in result.readlines()]


def walk_metadata(metadata_url, headers=None, expect_json=False):
    """ Walk the metadata tree and return a dictionary of the entire tree

        Args:
            metadata_url (str): metadata url
            headers (dict): headers to set for metadata request
            expect_json (bool): does the metadata_url return json
        Returns:
            dict: the result of walking the metadata tree
    """
    metadata = dict()

    for line in query_metadata(metadata_url, headers, expect_json):
        if line.endswith('/') and not line == 'public-keys/':
            key = line[:-1]
            metadata[key] = walk_metadata(metadata_url + line,
                                          headers, expect_json)
        else:
            results = query_metadata(metadata_url + line, headers,
                                     expect_json)
            if len(results) == 1:
                # disable pylint maybe-no-member because overloaded use of
                # the module name causes pylint to not detect that results
                # is an array or hash
                # pylint: disable=maybe-no-member
                metadata[line] = results.pop()
            else:
                metadata[line] = results
    return metadata


def get_provider_metadata(metadata_url, supports_recursive=False,
                          headers=None, expect_json=False):
    """ Retrieve the provider metadata

        Args:
            metadata_url (str): metadata url
            supports_recursive (bool): does the provider metadata api support
                                       recursion
            headers (dict): headers to set for metadata request
            expect_json (bool): does the metadata_url return json
        Returns:
            dict: the provider metadata
    """
    try:
        if supports_recursive:
            metadata = query_metadata(metadata_url, headers,
                                      expect_json)
        else:
            metadata = walk_metadata(metadata_url, headers,
                                     expect_json)
    except OpenShiftFactsMetadataUnavailableError:
        metadata = None
    return metadata


def normalize_gce_facts(metadata, facts):
    """ Normalize gce facts

        Args:
            metadata (dict): provider metadata
            facts (dict): facts to update
        Returns:
            dict: the result of adding the normalized metadata to the provided
                  facts dict
    """
    for interface in metadata['instance']['networkInterfaces']:
        int_info = dict(ips=[interface['ip']], network_type='gce')
        int_info['public_ips'] = [ac['externalIp'] for ac
                                  in interface['accessConfigs']]
        int_info['public_ips'].extend(interface['forwardedIps'])
        _, _, network_id = interface['network'].rpartition('/')
        int_info['network_id'] = network_id
        facts['network']['interfaces'].append(int_info)
    _, _, zone = metadata['instance']['zone'].rpartition('/')
    facts['zone'] = zone

    # GCE currently only supports a single interface
    facts['network']['ip'] = facts['network']['interfaces'][0]['ips'][0]
    pub_ip = facts['network']['interfaces'][0]['public_ips'][0]
    facts['network']['public_ip'] = pub_ip
    facts['network']['hostname'] = metadata['instance']['hostname']

    # TODO: attempt to resolve public_hostname
    facts['network']['public_hostname'] = facts['network']['public_ip']

    return facts


def normalize_aws_facts(metadata, facts):
    """ Normalize aws facts

        Args:
            metadata (dict): provider metadata
            facts (dict): facts to update
        Returns:
            dict: the result of adding the normalized metadata to the provided
                  facts dict
    """
    for interface in sorted(
            metadata['network']['interfaces']['macs'].values(),
            key=lambda x: x['device-number']
    ):
        int_info = dict()
        var_map = {'ips': 'local-ipv4s', 'public_ips': 'public-ipv4s'}
        for ips_var, int_var in var_map.iteritems():
            ips = interface.get(int_var)
            if isinstance(ips, basestring):
                int_info[ips_var] = [ips]
            else:
                int_info[ips_var] = ips
        if 'vpc-id' in interface:
            int_info['network_type'] = 'vpc'
        else:
            int_info['network_type'] = 'classic'
        if int_info['network_type'] == 'vpc':
            int_info['network_id'] = interface['subnet-id']
        else:
            int_info['network_id'] = None
        facts['network']['interfaces'].append(int_info)
    facts['zone'] = metadata['placement']['availability-zone']

    # TODO: actually attempt to determine default local and public ips
    # by using the ansible default ip fact and the ipv4-associations
    # from the ec2 metadata
    facts['network']['ip'] = metadata.get('local-ipv4')
    facts['network']['public_ip'] = metadata.get('public-ipv4')

    # TODO: verify that local hostname makes sense and is resolvable
    facts['network']['hostname'] = metadata.get('local-hostname')

    # TODO: verify that public hostname makes sense and is resolvable
    facts['network']['public_hostname'] = metadata.get('public-hostname')

    return facts


def normalize_openstack_facts(metadata, facts):
    """ Normalize openstack facts

        Args:
            metadata (dict): provider metadata
            facts (dict): facts to update
        Returns:
            dict: the result of adding the normalized metadata to the provided
                  facts dict
    """
    # openstack ec2 compat api does not support network interfaces and
    # the version tested on did not include the info in the openstack
    # metadata api, should be updated if neutron exposes this.

    facts['zone'] = metadata['availability_zone']
    local_ipv4 = metadata['ec2_compat']['local-ipv4'].split(',')[0]
    facts['network']['ip'] = local_ipv4
    facts['network']['public_ip'] = metadata['ec2_compat']['public-ipv4']

    # TODO: verify local hostname makes sense and is resolvable
    facts['network']['hostname'] = metadata['hostname']

    # TODO: verify that public hostname makes sense and is resolvable
    pub_h = metadata['ec2_compat']['public-hostname']
    facts['network']['public_hostname'] = pub_h

    return facts


def normalize_provider_facts(provider, metadata):
    """ Normalize provider facts

        Args:
            provider (str): host provider
            metadata (dict): provider metadata
        Returns:
            dict: the normalized provider facts
    """
    if provider is None or metadata is None:
        return {}

    # TODO: test for ipv6_enabled where possible (gce, aws do not support)
    # and configure ipv6 facts if available

    # TODO: add support for setting user_data if available

    facts = dict(name=provider, metadata=metadata,
                 network=dict(interfaces=[], ipv6_enabled=False))
    if os.path.exists('/etc/cloud.conf'):
        for arg in ('api_server_args', 'controller_args', 'kubelet_args'):
            facts[arg] = {'cloud-provider': [provider],
                          'cloud-config': ['/etc/cloud.conf']}

    if provider == 'gce':
        facts = normalize_gce_facts(metadata, facts)
    elif provider == 'ec2':
        facts = normalize_aws_facts(metadata, facts)
    elif provider == 'openstack':
        facts = normalize_openstack_facts(metadata, facts)
    return facts

def set_flannel_facts_if_unset(facts):
    """ Set flannel facts if not already present in facts dict
            dict: the facts dict updated with the flannel facts if
            missing
        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with the flannel
            facts if they were not already present

    """
    if 'common' in facts:
        if 'use_flannel' not in facts['common']:
            use_flannel = False
            facts['common']['use_flannel'] = use_flannel
    return facts

def set_nuage_facts_if_unset(facts):
    """ Set nuage facts if not already present in facts dict
            dict: the facts dict updated with the nuage facts if
            missing
        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with the nuage
            facts if they were not already present

    """
    if 'common' in facts:
        if 'use_nuage' not in facts['common']:
            use_nuage = False
            facts['common']['use_nuage'] = use_nuage
    return facts

def set_node_schedulability(facts):
    """ Set schedulable facts if not already present in facts dict
        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with the generated schedulable
            facts if they were not already present

    """
    if 'node' in facts:
        if 'schedulable' not in facts['node']:
            if 'master' in facts:
                facts['node']['schedulable'] = False
            else:
                facts['node']['schedulable'] = True
    return facts

def set_master_selectors(facts):
    """ Set selectors facts if not already present in facts dict
        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with the generated selectors
            facts if they were not already present

    """
    if 'master' in facts:
        if 'infra_nodes' in facts['master']:
            deployment_type = facts['common']['deployment_type']
            if deployment_type == 'online':
                selector = "type=infra"
            else:
                selector = "region=infra"

            if 'router_selector' not in facts['master']:
                facts['master']['router_selector'] = selector
            if 'registry_selector' not in facts['master']:
                facts['master']['registry_selector'] = selector
    return facts

def build_kubelet_args(facts):
    """ Build kubelet_args fact """
    if 'node' in facts:
        if 'kubelet_args' in facts['node']:
            kubelet_args = facts['node']['kubelet_args']
        else:
            kubelet_args = {}
        if 'read-only-port' not in kubelet_args and facts['common']['use_cluster_metrics']:
            kubelet_args['read-only-port'] = ['10255']
        if 'serialize-image-pulls' not in kubelet_args and facts['node']['parallel_pulls']:
            kubelet_args['serialize-image-pulls'] = facts['node']['parallel_pulls']

        facts['node']['kubelet_args'] = kubelet_args

    return facts

def set_identity_providers_if_unset(facts):
    """ Set identity_providers fact if not already present in facts dict

        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with the generated identity providers
            facts if they were not already present
    """
    if 'master' in facts:
        deployment_type = facts['common']['deployment_type']
        if 'identity_providers' not in facts['master']:
            identity_provider = dict(
                name='allow_all', challenge=True, login=True,
                kind='AllowAllPasswordIdentityProvider'
            )
            if deployment_type in ['enterprise', 'atomic-enterprise', 'openshift-enterprise']:
                identity_provider = dict(
                    name='deny_all', challenge=True, login=True,
                    kind='DenyAllPasswordIdentityProvider'
                )

            facts['master']['identity_providers'] = [identity_provider]

    return facts

def set_url_facts_if_unset(facts):
    """ Set url facts if not already present in facts dict

        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with the generated url facts if they
                  were not already present
    """
    if 'master' in facts:
        hostname = facts['common']['hostname']
        cluster_hostname = facts['master'].get('cluster_hostname')
        cluster_public_hostname = facts['master'].get('cluster_public_hostname')
        public_hostname = facts['common']['public_hostname']
        api_hostname = cluster_hostname if cluster_hostname else hostname
        api_public_hostname = cluster_public_hostname if cluster_public_hostname else public_hostname
        console_path = facts['master']['console_path']
        etcd_hosts = facts['master']['etcd_hosts']

        use_ssl = dict(
            api=facts['master']['api_use_ssl'],
            public_api=facts['master']['api_use_ssl'],
            loopback_api=facts['master']['api_use_ssl'],
            console=facts['master']['console_use_ssl'],
            public_console=facts['master']['console_use_ssl'],
            etcd=facts['master']['etcd_use_ssl']
        )

        ports = dict(
            api=facts['master']['api_port'],
            public_api=facts['master']['api_port'],
            loopback_api=facts['master']['api_port'],
            console=facts['master']['console_port'],
            public_console=facts['master']['console_port'],
            etcd=facts['master']['etcd_port'],
        )

        etcd_urls = []
        if etcd_hosts != '':
            facts['master']['etcd_port'] = ports['etcd']
            facts['master']['embedded_etcd'] = False
            for host in etcd_hosts:
                etcd_urls.append(format_url(use_ssl['etcd'], host,
                                            ports['etcd']))
        else:
            etcd_urls = [format_url(use_ssl['etcd'], hostname,
                                    ports['etcd'])]

        facts['master'].setdefault('etcd_urls', etcd_urls)

        prefix_hosts = [('api', api_hostname),
                        ('public_api', api_public_hostname),
                        ('loopback_api', hostname)]

        for prefix, host in prefix_hosts:
            facts['master'].setdefault(prefix + '_url', format_url(use_ssl[prefix],
                                                                   host,
                                                                   ports[prefix]))


        r_lhn = "{0}:{1}".format(hostname, ports['api']).replace('.', '-')
        r_lhu = "system:openshift-master/{0}:{1}".format(api_hostname, ports['api']).replace('.', '-')
        facts['master'].setdefault('loopback_cluster_name', r_lhn)
        facts['master'].setdefault('loopback_context_name', "default/{0}/system:openshift-master".format(r_lhn))
        facts['master'].setdefault('loopback_user', r_lhu)

        prefix_hosts = [('console', api_hostname), ('public_console', api_public_hostname)]
        for prefix, host in prefix_hosts:
            facts['master'].setdefault(prefix + '_url', format_url(use_ssl[prefix],
                                                                   host,
                                                                   ports[prefix],
                                                                   console_path))

    return facts

def set_aggregate_facts(facts):
    """ Set aggregate facts

        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with aggregated facts
    """
    all_hostnames = set()
    internal_hostnames = set()
    if 'common' in facts:
        all_hostnames.add(facts['common']['hostname'])
        all_hostnames.add(facts['common']['public_hostname'])
        all_hostnames.add(facts['common']['ip'])
        all_hostnames.add(facts['common']['public_ip'])

        internal_hostnames.add(facts['common']['hostname'])
        internal_hostnames.add(facts['common']['ip'])

        cluster_domain = facts['common']['dns_domain']

        if 'master' in facts:
            if 'cluster_hostname' in facts['master']:
                all_hostnames.add(facts['master']['cluster_hostname'])
            if 'cluster_public_hostname' in facts['master']:
                all_hostnames.add(facts['master']['cluster_public_hostname'])
            svc_names = ['openshift', 'openshift.default', 'openshift.default.svc',
                         'openshift.default.svc.' + cluster_domain, 'kubernetes', 'kubernetes.default',
                         'kubernetes.default.svc', 'kubernetes.default.svc.' + cluster_domain]
            all_hostnames.update(svc_names)
            internal_hostnames.update(svc_names)
            first_svc_ip = first_ip(facts['master']['portal_net'])
            all_hostnames.add(first_svc_ip)
            internal_hostnames.add(first_svc_ip)

        facts['common']['all_hostnames'] = list(all_hostnames)
        facts['common']['internal_hostnames'] = list(internal_hostnames)

    return facts


def set_etcd_facts_if_unset(facts):
    """
    If using embedded etcd, loads the data directory from master-config.yaml.

    If using standalone etcd, loads ETCD_DATA_DIR from etcd.conf.

    If anything goes wrong parsing these, the fact will not be set.
    """
    if 'master' in facts and facts['master']['embedded_etcd']:
        etcd_facts = facts['etcd'] if 'etcd' in facts else dict()

        if 'etcd_data_dir' not in etcd_facts:
            try:
                # Parse master config to find actual etcd data dir:
                master_cfg_path = os.path.join(facts['common']['config_base'],
                                               'master/master-config.yaml')
                master_cfg_f = open(master_cfg_path, 'r')
                config = yaml.safe_load(master_cfg_f.read())
                master_cfg_f.close()

                etcd_facts['etcd_data_dir'] = \
                    config['etcdConfig']['storageDirectory']

                facts['etcd'] = etcd_facts

            # We don't want exceptions bubbling up here:
            # pylint: disable=broad-except
            except Exception:
                pass
    else:
        etcd_facts = facts['etcd'] if 'etcd' in facts else dict()

        # Read ETCD_DATA_DIR from /etc/etcd/etcd.conf:
        try:
            # Add a fake section for parsing:
            ini_str = '[root]\n' + open('/etc/etcd/etcd.conf', 'r').read()
            ini_fp = StringIO.StringIO(ini_str)
            config = ConfigParser.RawConfigParser()
            config.readfp(ini_fp)
            etcd_data_dir = config.get('root', 'ETCD_DATA_DIR')
            if etcd_data_dir.startswith('"') and etcd_data_dir.endswith('"'):
                etcd_data_dir = etcd_data_dir[1:-1]

            etcd_facts['etcd_data_dir'] = etcd_data_dir
            facts['etcd'] = etcd_facts

        # We don't want exceptions bubbling up here:
        # pylint: disable=broad-except
        except Exception:
            pass

    return facts

def set_deployment_facts_if_unset(facts):
    """ Set Facts that vary based on deployment_type.

        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with the generated deployment_type
            facts
    """
    # disabled to avoid breaking up facts related to deployment type into
    # multiple methods for now.
    # pylint: disable=too-many-statements, too-many-branches
    if 'common' in facts:
        deployment_type = facts['common']['deployment_type']
        config_base = facts['common']['config_base']
        data_dir = facts['common']['data_dir']
        # Handle upgrade scenarios when symlinks don't yet exist:
        if not os.path.exists(config_base) and os.path.exists('/etc/openshift'):
            facts['common']['config_base'] = '/etc/openshift'
        if not os.path.exists(data_dir) and os.path.exists('/var/lib/openshift'):
            facts['common']['data_dir'] = '/var/lib/openshift'

    if 'docker' in facts:
        deployment_type = facts['common']['deployment_type']
        if deployment_type in ['enterprise', 'atomic-enterprise', 'openshift-enterprise']:
            addtl_regs = facts['docker'].get('additional_registries', [])
            ent_reg = 'registry.access.redhat.com'
            if ent_reg not in addtl_regs:
                facts['docker']['additional_registries'] = addtl_regs + [ent_reg]

    if 'master' in facts:
        deployment_type = facts['common']['deployment_type']
        openshift_features = ['Builder', 'S2IBuilder', 'WebConsole']
        if 'disabled_features' in facts['master']:
            if deployment_type == 'atomic-enterprise':
                curr_disabled_features = set(facts['master']['disabled_features'])
                facts['master']['disabled_features'] = list(curr_disabled_features.union(openshift_features))
        else:
            if deployment_type == 'atomic-enterprise':
                facts['master']['disabled_features'] = openshift_features

    return facts

def set_sdn_facts_if_unset(facts, system_facts):
    """ Set sdn facts if not already present in facts dict

        Args:
            facts (dict): existing facts
            system_facts (dict): ansible_facts
        Returns:
            dict: the facts dict updated with the generated sdn facts if they
                  were not already present
    """
    if 'common' in facts:
        use_sdn = facts['common']['use_openshift_sdn']
        if not (use_sdn == '' or isinstance(use_sdn, bool)):
            use_sdn = safe_get_bool(use_sdn)
            facts['common']['use_openshift_sdn'] = use_sdn
        if 'sdn_network_plugin_name' not in facts['common']:
            plugin = 'redhat/openshift-ovs-subnet' if use_sdn else ''
            facts['common']['sdn_network_plugin_name'] = plugin

    if 'master' in facts:
        if 'sdn_cluster_network_cidr' not in facts['master']:
            facts['master']['sdn_cluster_network_cidr'] = '10.1.0.0/16'
        if 'sdn_host_subnet_length' not in facts['master']:
            facts['master']['sdn_host_subnet_length'] = '8'

    if 'node' in facts and 'sdn_mtu' not in facts['node']:
        node_ip = facts['common']['ip']

        # default MTU if interface MTU cannot be detected
        facts['node']['sdn_mtu'] = '1450'

        for val in system_facts.itervalues():
            if isinstance(val, dict) and 'mtu' in val:
                mtu = val['mtu']

                if 'ipv4' in val and val['ipv4'].get('address') == node_ip:
                    facts['node']['sdn_mtu'] = str(mtu - 50)

    return facts

def format_url(use_ssl, hostname, port, path=''):
    """ Format url based on ssl flag, hostname, port and path

        Args:
            use_ssl (bool): is ssl enabled
            hostname (str): hostname
            port (str): port
            path (str): url path
        Returns:
            str: The generated url string
    """
    scheme = 'https' if use_ssl else 'http'
    netloc = hostname
    if (use_ssl and port != '443') or (not use_ssl and port != '80'):
        netloc += ":%s" % port
    return urlparse.urlunparse((scheme, netloc, path, '', '', ''))

def get_current_config(facts):
    """ Get current openshift config

        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with the current openshift config
    """
    current_config = dict()
    roles = [role for role in facts if role not in ['common', 'provider']]
    for role in roles:
        if 'roles' in current_config:
            current_config['roles'].append(role)
        else:
            current_config['roles'] = [role]

        # TODO: parse the /etc/sysconfig/openshift-{master,node} config to
        # determine the location of files.
        # TODO: I suspect this isn't working right now, but it doesn't prevent
        # anything from working properly as far as I can tell, perhaps because
        # we override the kubeconfig path everywhere we use it?
        # Query kubeconfig settings
        kubeconfig_dir = '/var/lib/origin/openshift.local.certificates'
        if role == 'node':
            kubeconfig_dir = os.path.join(
                kubeconfig_dir, "node-%s" % facts['common']['hostname']
            )

        kubeconfig_path = os.path.join(kubeconfig_dir, '.kubeconfig')
        if (os.path.isfile('/usr/bin/openshift')
                and os.path.isfile(kubeconfig_path)):
            try:
                _, output, _ = module.run_command(
                    ["/usr/bin/openshift", "ex", "config", "view", "-o",
                     "json", "--kubeconfig=%s" % kubeconfig_path],
                    check_rc=False
                )
                config = json.loads(output)

                cad = 'certificate-authority-data'
                try:
                    for cluster in config['clusters']:
                        config['clusters'][cluster][cad] = 'masked'
                except KeyError:
                    pass
                try:
                    for user in config['users']:
                        config['users'][user][cad] = 'masked'
                        config['users'][user]['client-key-data'] = 'masked'
                except KeyError:
                    pass

                current_config['kubeconfig'] = config

            # override pylint broad-except warning, since we do not want
            # to bubble up any exceptions if oc config view
            # fails
            # pylint: disable=broad-except
            except Exception:
                pass

    return current_config

def get_version_output(binary, version_cmd):
    """ runs and returns the version output for a command """
    cmd = []
    for item in (binary, version_cmd):
        if isinstance(item, list):
            cmd.extend(item)
        else:
            cmd.append(item)

    if os.path.isfile(cmd[0]):
        _, output, _ = module.run_command(cmd)
    return output

def docker_parse_version(binary='/usr/bin/docker'):
    """ Parses and returns the docker version info """
    version_info = yaml.safe_load(get_version_output(binary, 'version'))
    result = {
        'api_version': version_info['Server']['API version'],
        'version': version_info['Server']['Version']
    }
    return result

def etcd_parse_version(binary='/usr/bin/etcd'):
    """ Parses and returns the etcd version info """
    version_info = yaml.safe_load(get_version_output(binary, '--version'))
    result = {'version': version_info['etcd Version']}
    return result

def openshift_parse_version(binary='/usr/bin/openshift'):
    """ Parses and returns the openshift version info """
    version_info = yaml.safe_load(get_version_output(binary, 'version').replace(" ", ": "))
    result = {
        'version': version_info['openshift'][1:],
        'kubernetes_version': version_info['kubernetes'][1:],
        'etcd_version': version_info['etcd']
    }
    return result

def get_installed_package_versions():
    """ Get current version of packages installed on the host

        Returns:
            versions(dict): dictionary of package name to package attributes
    """
    # TODO: support containerized versions
    versions = {}

    openshift_service_defaults = {
        'binary': '/usr/bin/openshift',
        'version_method': openshift_parse_version
    }

    services = {
        'docker': {
            'binary': '/usr/bin/docker',
            'version_method': docker_parse_version
        },
        'etcd': {
            'binary': '/usr/bin/etcd',
            'version_method': etcd_parse_version
        },
        'atomic-openshift-node': openshift_service_defaults,
        'atomic-openshift-master': openshift_service_defaults,
        'atomic-openshift-master-api': openshift_service_defaults,
        'origin-node': openshift_service_defaults,
        'origin-master': openshift_service_defaults,
        'origin-master-api': openshift_service_defaults
    }

    bus = SystemBus()
    systemd = bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
    manager = Interface(systemd, dbus_interface='org.freedesktop.systemd1.Manager')

    for service in services.keys():
        try:
            service_unit = manager.GetUnit('{0}.service'.format(service))
            service_proxy = bus.get_object('org.freedesktop.systemd1', str(service_unit))
            service_properties = Interface(service_proxy, dbus_interface='org.freedesktop.DBus.Properties')
            service_load_state = service_properties.Get('org.freedesktop.systemd1.Unit', 'LoadState')
            service_active_state = service_properties.Get('org.freedesktop.systemd1.Unit', 'ActiveState')
            if service_load_state == 'loaded' and service_active_state == 'active':
                versions[service] = services[service]['version_method']()
                if service.split('-')[-1] == 'node' and 'etcd_version' in versions[service]:
                    del versions[service]['etcd_version']
        except DBusException:
            pass

    return versions


def get_openshift_version(facts, cli_image=None):
    """ Get current version of openshift on the host

        Args:
            facts (dict): existing facts
            optional cli_image for pulling the version number

        Returns:
            version: the current openshift version
    """
    version = None

    # No need to run this method repeatedly on a system if we already know the
    # version
    if 'common' in facts:
        if 'version' in facts['common'] and facts['common']['version'] is not None:
            return facts['common']['version']

    if os.path.isfile('/usr/bin/openshift'):
        _, output, _ = module.run_command(['/usr/bin/openshift', 'version'])
        version = parse_openshift_version(output)

    if 'is_containerized' in facts['common'] and safe_get_bool(facts['common']['is_containerized']):
        container = None
        if 'master' in facts:
            if 'cluster_method' in facts['master']:
                container = facts['common']['service_type'] + '-master-api'
            else:
                container = facts['common']['service_type'] + '-master'
        elif 'node' in facts:
            container = facts['common']['service_type'] + '-node'

        if container is not None:
            exit_code, output, _ = module.run_command(['docker', 'exec', container, 'openshift', 'version'])
            # if for some reason the container is installed but not running
            # we'll fall back to using docker run later in this method.
            if exit_code == 0:
                version = parse_openshift_version(output)

        if version is None and cli_image is not None:
            # Assume we haven't installed the environment yet and we need
            # to query the latest image
            exit_code, output, _ = module.run_command(['docker', 'run', '--rm', cli_image, 'version'])
            version = parse_openshift_version(output)

    return version

def parse_openshift_version(output):
    """ Apply provider facts to supplied facts dict

        Args:
            string: output of 'openshift version'
        Returns:
            string: the version number
    """
    versions = dict(e.split(' v') for e in output.splitlines() if ' v' in e)
    return versions.get('openshift', '')


def apply_provider_facts(facts, provider_facts):
    """ Apply provider facts to supplied facts dict

        Args:
            facts (dict): facts dict to update
            provider_facts (dict): provider facts to apply
            roles: host roles
        Returns:
            dict: the merged facts
    """
    if not provider_facts:
        return facts

    common_vars = [('hostname', 'ip'), ('public_hostname', 'public_ip')]
    for h_var, ip_var in common_vars:
        ip_value = provider_facts['network'].get(ip_var)
        if ip_value:
            facts['common'][ip_var] = ip_value

        facts['common'][h_var] = choose_hostname(
            [provider_facts['network'].get(h_var)],
            facts['common'][ip_var]
        )

    facts['provider'] = provider_facts
    return facts

# Disabling pylint too many branches. This function needs refactored
# but is a very core part of openshift_facts.
# pylint: disable=too-many-branches
def merge_facts(orig, new, additive_facts_to_overwrite, protected_facts_to_overwrite):
    """ Recursively merge facts dicts

        Args:
            orig (dict): existing facts
            new (dict): facts to update
            additive_facts_to_overwrite (list): additive facts to overwrite in jinja
                                                '.' notation ex: ['master.named_certificates']
            protected_facts_to_overwrite (list): protected facts to overwrite in jinja
                                                 '.' notation ex: ['master.master_count']

        Returns:
            dict: the merged facts
    """
    additive_facts = ['named_certificates']
    protected_facts = ['ha', 'master_count']
    facts = dict()
    for key, value in orig.iteritems():
        # Key exists in both old and new facts.
        if key in new:
            # Continue to recurse if old and new fact is a dictionary.
            if isinstance(value, dict) and isinstance(new[key], dict):
                # Collect the subset of additive facts to overwrite if
                # key matches. These will be passed to the subsequent
                # merge_facts call.
                relevant_additive_facts = []
                for item in additive_facts_to_overwrite:
                    if '.' in item and item.startswith(key + '.'):
                        relevant_additive_facts.append(item)

                # Collect the subset of protected facts to overwrite
                # if key matches. These will be passed to the
                # subsequent merge_facts call.
                relevant_protected_facts = []
                for item in protected_facts_to_overwrite:
                    if '.' in item and item.startswith(key + '.'):
                        relevant_protected_facts.append(item)
                facts[key] = merge_facts(value, new[key], relevant_additive_facts, relevant_protected_facts)
            # Key matches an additive fact and we are not overwriting
            # it so we will append the new value to the existing value.
            elif key in additive_facts and key not in [x.split('.')[-1] for x in additive_facts_to_overwrite]:
                if isinstance(value, list) and isinstance(new[key], list):
                    new_fact = []
                    for item in copy.deepcopy(value) + copy.deepcopy(new[key]):
                        if item not in new_fact:
                            new_fact.append(item)
                    facts[key] = new_fact
            # Key matches a protected fact and we are not overwriting
            # it so we will determine if it is okay to change this
            # fact.
            elif key in protected_facts and key not in [x.split('.')[-1] for x in protected_facts_to_overwrite]:
                # The master count (int) can only increase unless it
                # has been passed as a protected fact to overwrite.
                if key == 'master_count':
                    if int(value) <= int(new[key]):
                        facts[key] = copy.deepcopy(new[key])
                    else:
                        module.fail_json(msg='openshift_facts received a lower value for openshift.master.master_count')
                # ha (bool) can not change unless it has been passed
                # as a protected fact to overwrite.
                if key == 'ha':
                    if safe_get_bool(value) != safe_get_bool(new[key]):
                        module.fail_json(msg='openshift_facts received a different value for openshift.master.ha')
                    else:
                        facts[key] = value
            # No other condition has been met. Overwrite the old fact
            # with the new value.
            else:
                facts[key] = copy.deepcopy(new[key])
        # Key isn't in new so add it to facts to keep it.
        else:
            facts[key] = copy.deepcopy(value)
    new_keys = set(new.keys()) - set(orig.keys())
    for key in new_keys:
        facts[key] = copy.deepcopy(new[key])
    return facts


def merge_provider_facts(facts):
    """ Recursively merge provider facts dicts

        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with the provider config
    """
    if 'provider' not in facts:
        return facts
    if 'master' in facts:
        for arg in ('api_server_args', 'controller_args'):
            facts['master'][arg] = merge_facts(
                facts['provider'].get(arg, {}),
                facts['master'].get(arg, {}),
                [], [])
    if 'node' in facts:
        facts['node']['kubelet_args'] = merge_facts(
            facts['provider'].get('kubelet_args', {}),
            facts['node'].get('kubelet_args', {}),
            [], [])
    return facts


def save_local_facts(filename, facts):
    """ Save local facts

        Args:
            filename (str): local facts file
            facts (dict): facts to set
    """
    try:
        fact_dir = os.path.dirname(filename)
        if not os.path.exists(fact_dir):
            os.makedirs(fact_dir)
        with open(filename, 'w') as fact_file:
            fact_file.write(module.jsonify(facts))
        os.chmod(filename, 0o600)
    except (IOError, OSError) as ex:
        raise OpenShiftFactsFileWriteError(
            "Could not create fact file: %s, error: %s" % (filename, ex)
        )


def get_local_facts_from_file(filename):
    """ Retrieve local facts from fact file

        Args:
            filename (str): local facts file
        Returns:
            dict: the retrieved facts
    """
    local_facts = dict()
    try:
        # Handle conversion of INI style facts file to json style
        ini_facts = ConfigParser.SafeConfigParser()
        ini_facts.read(filename)
        for section in ini_facts.sections():
            local_facts[section] = dict()
            for key, value in ini_facts.items(section):
                local_facts[section][key] = value

    except (ConfigParser.MissingSectionHeaderError,
            ConfigParser.ParsingError):
        try:
            with open(filename, 'r') as facts_file:
                local_facts = json.load(facts_file)
        except (ValueError, IOError):
            pass

    return local_facts

def safe_get_bool(fact):
    """ Get a boolean fact safely.

        Args:
            facts: fact to convert
        Returns:
            bool: given fact as a bool
    """
    return bool(strtobool(str(fact)))

def set_container_facts_if_unset(facts):
    """ Set containerized facts.

        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with the generated containerization
            facts
    """
    deployment_type = facts['common']['deployment_type']
    if deployment_type in ['enterprise', 'openshift-enterprise']:
        master_image = 'openshift3/ose'
        cli_image = master_image
        node_image = 'openshift3/node'
        ovs_image = 'openshift3/openvswitch'
        etcd_image = 'registry.access.redhat.com/rhel7/etcd'
    elif deployment_type == 'atomic-enterprise':
        master_image = 'aep3_beta/aep'
        cli_image = master_image
        node_image = 'aep3_beta/node'
        ovs_image = 'aep3_beta/openvswitch'
        etcd_image = 'registry.access.redhat.com/rhel7/etcd'
    else:
        master_image = 'openshift/origin'
        cli_image = master_image
        node_image = 'openshift/node'
        ovs_image = 'openshift/openvswitch'
        etcd_image = 'registry.access.redhat.com/rhel7/etcd'

    facts['common']['is_atomic'] = os.path.isfile('/run/ostree-booted')
    if 'is_containerized' not in facts['common']:
        facts['common']['is_containerized'] = facts['common']['is_atomic']
    if 'cli_image' not in facts['common']:
        facts['common']['cli_image'] = cli_image
    if 'etcd' in facts and 'etcd_image' not in facts['etcd']:
        facts['etcd']['etcd_image'] = etcd_image
    if 'master' in facts and 'master_image' not in facts['master']:
        facts['master']['master_image'] = master_image
    if 'node' in facts:
        if 'node_image' not in facts['node']:
            facts['node']['node_image'] = node_image
        if 'ovs_image' not in facts['node']:
            facts['node']['ovs_image'] = ovs_image

    if safe_get_bool(facts['common']['is_containerized']):
        facts['common']['admin_binary'] = '/usr/local/bin/oadm'
        facts['common']['client_binary'] = '/usr/local/bin/oc'
        base_version = get_openshift_version(facts, cli_image).split('-')[0]
        facts['common']['image_tag'] = "v" + base_version

    return facts

def set_installed_variant_rpm_facts(facts):
    """ Set RPM facts of installed variant
        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with installed_variant_rpms
                          """
    installed_rpms = []
    for base_rpm in ['openshift', 'atomic-openshift', 'origin']:
        optional_rpms = ['master', 'node', 'clients', 'sdn-ovs']
        variant_rpms = [base_rpm] + \
                       ['{0}-{1}'.format(base_rpm, r) for r in optional_rpms] + \
                       ['tuned-profiles-%s-node' % base_rpm]
        for rpm in variant_rpms:
            exit_code, _, _ = module.run_command(['rpm', '-q', rpm])
            if exit_code == 0:
                installed_rpms.append(rpm)

    facts['common']['installed_variant_rpms'] = installed_rpms
    return facts



class OpenShiftFactsInternalError(Exception):
    """Origin Facts Error"""
    pass


class OpenShiftFactsUnsupportedRoleError(Exception):
    """Origin Facts Unsupported Role Error"""
    pass


class OpenShiftFactsFileWriteError(Exception):
    """Origin Facts File Write Error"""
    pass


class OpenShiftFactsMetadataUnavailableError(Exception):
    """Origin Facts Metadata Unavailable Error"""
    pass


class OpenShiftFacts(object):
    """ Origin Facts

        Attributes:
            facts (dict): facts for the host

        Args:
            module (AnsibleModule): an AnsibleModule object
            role (str): role for setting local facts
            filename (str): local facts file to use
            local_facts (dict): local facts to set
            additive_facts_to_overwrite (list): additive facts to overwrite in jinja
                                                '.' notation ex: ['master.named_certificates']
            protected_facts_to_overwrite (list): protected facts to overwrite in jinja
                                                 '.' notation ex: ['master.master_count']

        Raises:
            OpenShiftFactsUnsupportedRoleError:
    """
    known_roles = ['common', 'master', 'node', 'etcd', 'hosted', 'docker']

    # Disabling too-many-arguments, this should be cleaned up as a TODO item.
    # pylint: disable=too-many-arguments
    def __init__(self, role, filename, local_facts,
                 additive_facts_to_overwrite=None,
                 openshift_env=None,
                 protected_facts_to_overwrite=None):
        self.changed = False
        self.filename = filename
        if role not in self.known_roles:
            raise OpenShiftFactsUnsupportedRoleError(
                "Role %s is not supported by this module" % role
            )
        self.role = role
        self.system_facts = ansible_facts(module)
        self.facts = self.generate_facts(local_facts,
                                         additive_facts_to_overwrite,
                                         openshift_env,
                                         protected_facts_to_overwrite)

    def generate_facts(self,
                       local_facts,
                       additive_facts_to_overwrite,
                       openshift_env,
                       protected_facts_to_overwrite):
        """ Generate facts

            Args:
                local_facts (dict): local_facts for overriding generated defaults
                additive_facts_to_overwrite (list): additive facts to overwrite in jinja
                                                    '.' notation ex: ['master.named_certificates']
                openshift_env (dict): openshift_env facts for overriding generated defaults
                protected_facts_to_overwrite (list): protected facts to overwrite in jinja
                                                     '.' notation ex: ['master.master_count']
            Returns:
                dict: The generated facts
        """
        local_facts = self.init_local_facts(local_facts,
                                            additive_facts_to_overwrite,
                                            openshift_env,
                                            protected_facts_to_overwrite)
        roles = local_facts.keys()


        if 'common' in local_facts and 'deployment_type' in local_facts['common']:
            deployment_type = local_facts['common']['deployment_type']
        else:
            deployment_type = 'origin'

        if 'common' in local_facts and 'is_containerized' in local_facts['common']:
            is_containerized = local_facts['common']['is_containerized']
        else:
            is_containerized = False


        defaults = self.get_defaults(roles, deployment_type, is_containerized)
        provider_facts = self.init_provider_facts()
        facts = apply_provider_facts(defaults, provider_facts)
        facts = merge_facts(facts,
                            local_facts,
                            additive_facts_to_overwrite,
                            protected_facts_to_overwrite)
        facts = merge_provider_facts(facts)
        facts['current_config'] = get_current_config(facts)
        facts = build_kubelet_args(facts)
        facts = set_url_facts_if_unset(facts)
        facts = set_flannel_facts_if_unset(facts)
        facts = set_nuage_facts_if_unset(facts)
        facts = set_node_schedulability(facts)
        facts = set_master_selectors(facts)
        facts = set_identity_providers_if_unset(facts)
        facts = set_sdn_facts_if_unset(facts, self.system_facts)
        facts = set_deployment_facts_if_unset(facts)
        facts = set_aggregate_facts(facts)
        facts = set_etcd_facts_if_unset(facts)
        facts = set_container_facts_if_unset(facts)
        if not safe_get_bool(facts['common']['is_containerized']):
            facts = set_installed_variant_rpm_facts(facts)
        return dict(openshift=facts)

    # disabled to avoid breaking up get_defaults into
    # multiple methods for now.
    # pylint: disable=too-many-statements, too-many-branches, too-many-locals
    def get_defaults(self, roles, deployment_type, is_containerized):
        """ Get default fact values

            Args:
                roles (list): list of roles for this host

            Returns:
                dict: The generated default facts
        """
        defaults = {'installed_versions': get_installed_package_versions()}
        ip_addr = self.system_facts['default_ipv4']['address']
        exit_code, output, _ = module.run_command(['hostname', '-f'])
        hostname_f = output.strip() if exit_code == 0 else ''
        hostname_values = [hostname_f, self.system_facts['nodename'],
                           self.system_facts['fqdn']]
        hostname = choose_hostname(hostname_values, ip_addr)

        is_atomic = os.path.isfile('/run/ostree-booted')
        if not is_containerized and is_atomic:
            is_containerized = True

        # Update this to use installed_versions
        version = get_openshift_version(dict(common=dict(is_containerized=is_containerized)))

        if version is not None:
            if deployment_type == 'origin':
                version_gte_3_1_or_1_1 = LooseVersion(version) >= LooseVersion('1.1.0')
                version_gte_3_1_1_or_1_1_1 = LooseVersion(version) >= LooseVersion('1.1.1')
                version_gte_3_2_or_1_2 = LooseVersion(version) >= LooseVersion('1.2.0')
            else:
                version_gte_3_1_or_1_1 = LooseVersion(version) >= LooseVersion('3.0.2.905')
                version_gte_3_1_1_or_1_1_1 = LooseVersion(version) >= LooseVersion('3.1.1')
                version_gte_3_2_or_1_2 = LooseVersion(version) >= LooseVersion('3.1.1.901')
        else:
            version_gte_3_1_or_1_1 = True
            version_gte_3_1_1_or_1_1_1 = True
            version_gte_3_2_or_1_2 = True

        if deployment_type == 'atomic-enterprise' and not version_gte_3_2_or_1_2:
            dt_key = 'atomic-enterprise-beta'
        else:
            dt_key = deployment_type

        admin_binary = '/usr/local/bin/oadm' if is_containerized else 'oadm'
        client_binary = '/usr/local/bin/oc' if is_containerized else 'oc'

        defaults['common'] = dict(
            use_openshift_sdn=True, ip=ip_addr, public_ip=ip_addr,
            deployment_type=deployment_type, hostname=hostname,
            public_hostname=hostname, client_binary=client_binary,
            admin_binary=admin_binary, dns_domain='cluster.local',
            install_examples=True, debug_level=2, use_cluster_metrics=False,
            is_atomic=is_atomic, is_containerized=is_containerized,
            service_type=DEPLOYMENT_TYPE_VALUES[dt_key]['service_type'],
            config_base=DEPLOYMENT_TYPE_VALUES[dt_key]['config_base'],
            data_dir=DEPLOYMENT_TYPE_VALUES[dt_key]['data_dir'],
            version_gte_3_1_or_1_1=version_gte_3_1_or_1_1,
            version_gte_3_1_1_or_1_1_1=version_gte_3_1_1_or_1_1_1,
            version_gte_3_2_or_1_2=version_gte_3_2_or_1_2,
            use_manageiq=version_gte_3_1_or_1_1,
            cli_image=DEPLOYMENT_TYPE_VALUES[dt_key]['cli_image']
        )

        registry_url = 'openshift/origin-${component}:${version}'
        if deployment_type in ['enterprise', 'online', 'openshift-enterprise']:
            registry_url = 'openshift3/ose-${component}:${version}'
        elif deployment_type == 'atomic-enterprise':
            if version_gte_3_2_or_1_2:
                registry_url = 'aep3/aep-${component}:${version}'
            else:
                registry_url = 'aep3_beta/aep-${component}:${version}'

        if 'etcd' in roles:
            defaults['etcd'] = dict(
                etcd_image=DEPLOYMENT_TYPE_VALUES[dt_key]['etcd_image']
            )

        if 'master' in roles:
            defaults['master'] = dict(
                api_use_ssl=True, api_port='8443', controllers_port='8444',
                console_use_ssl=True, console_path='/console',
                console_port='8443', etcd_use_ssl=True, etcd_hosts='',
                etcd_port='4001', portal_net='172.30.0.0/16',
                embedded_etcd=True, embedded_kube=True,
                embedded_dns=True, dns_port='53', bind_addr='0.0.0.0',
                session_max_seconds=3600, session_name='ssn',
                session_secrets_file='', access_token_max_seconds=86400,
                auth_token_max_seconds=500, oauth_grant_method='auto',
                registry_url=registry_url, default_node_selector='',
                project_request_message='', project_request_template='',
                mcs_allocator_range='s0:/2', mcs_labels_per_project=5,
                uid_allocator_range='1000000000-1999999999/10000',
                master_image=DEPLOYMENT_TYPE_VALUES[dt_key]['master_image']
            )

        if 'node' in roles:
            parallel_pulls = False
            if 'docker' in defaults['installed_versions']:
                docker_version = defaults['installed_versions']['docker']['version']
                if LooseVersion(docker_version) >= LooseVersion('1.9'):
                    parallel_pulls = True

            defaults['node'] = dict(
                labels={}, annotations={}, portal_net='172.30.0.0/16',
                iptables_sync_period='5s', set_node_ip=False,
                registry_url='registry_url',
                node_image=DEPLOYMENT_TYPE_VALUES[dt_key]['node_image'],
                ovs_image=DEPLOYMENT_TYPE_VALUES[dt_key]['ovs_image'],
                storage_plugin_deps=['ceph', 'glusterfs', 'iscsi', 'nfs'],
                parallel_pulls=parallel_pulls
            )

        if 'docker' in roles:
            defaults['docker'] = dict(disable_push_dockerhub=False)

        if 'hosted' in roles:
            defaults['hosted'] = dict(
                registry=dict(
                    storage=dict(
                        kind=None,
                        volume=dict(
                            name='registry',
                            size='5Gi'
                        ),
                        nfs=dict(
                            directory='/exports',
                            options='*(rw,root_squash)'),
                        host=None,
                        access_modes=['ReadWriteMany'],
                        create_pv=True
                    )
                )
            )

        return defaults

    def guess_host_provider(self):
        """ Guess the host provider

            Returns:
                dict: The generated default facts for the detected provider
        """
        # TODO: cloud provider facts should probably be submitted upstream
        product_name = self.system_facts['product_name']
        product_version = self.system_facts['product_version']
        virt_type = self.system_facts['virtualization_type']
        virt_role = self.system_facts['virtualization_role']
        provider = None
        metadata = None

        # TODO: this is not exposed through module_utils/facts.py in ansible,
        # need to create PR for ansible to expose it
        bios_vendor = get_file_content(
            '/sys/devices/virtual/dmi/id/bios_vendor'
        )
        if bios_vendor == 'Google':
            provider = 'gce'
            metadata_url = ('http://metadata.google.internal/'
                            'computeMetadata/v1/?recursive=true')
            headers = {'Metadata-Flavor': 'Google'}
            metadata = get_provider_metadata(metadata_url, True, headers,
                                             True)

            # Filter sshKeys and serviceAccounts from gce metadata
            if metadata:
                metadata['project']['attributes'].pop('sshKeys', None)
                metadata['instance'].pop('serviceAccounts', None)
        elif (virt_type == 'xen' and virt_role == 'guest'
              and re.match(r'.*\.amazon$', product_version)):
            provider = 'ec2'
            metadata_url = 'http://169.254.169.254/latest/meta-data/'
            metadata = get_provider_metadata(metadata_url)
        elif re.search(r'OpenStack', product_name):
            provider = 'openstack'
            metadata_url = ('http://169.254.169.254/openstack/latest/'
                            'meta_data.json')
            metadata = get_provider_metadata(metadata_url, True, None,
                                             True)

            if metadata:
                ec2_compat_url = 'http://169.254.169.254/latest/meta-data/'
                metadata['ec2_compat'] = get_provider_metadata(
                    ec2_compat_url
                )

                # disable pylint maybe-no-member because overloaded use of
                # the module name causes pylint to not detect that results
                # is an array or hash
                # pylint: disable=maybe-no-member
                # Filter public_keys  and random_seed from openstack metadata
                metadata.pop('public_keys', None)
                metadata.pop('random_seed', None)

                if not metadata['ec2_compat']:
                    metadata = None

        return dict(name=provider, metadata=metadata)

    def init_provider_facts(self):
        """ Initialize the provider facts

            Returns:
                dict: The normalized provider facts
        """
        provider_info = self.guess_host_provider()
        provider_facts = normalize_provider_facts(
            provider_info.get('name'),
            provider_info.get('metadata')
        )
        return provider_facts

    # Disabling too-many-branches. This should be cleaned up as a TODO item.
    #pylint: disable=too-many-branches
    def init_local_facts(self, facts=None,
                         additive_facts_to_overwrite=None,
                         openshift_env=None,
                         protected_facts_to_overwrite=None):
        """ Initialize the local facts

            Args:
                facts (dict): local facts to set
                additive_facts_to_overwrite (list): additive facts to overwrite in jinja
                                                    '.' notation ex: ['master.named_certificates']
                openshift_env (dict): openshift env facts to set
                protected_facts_to_overwrite (list): protected facts to overwrite in jinja
                                                     '.' notation ex: ['master.master_count']


            Returns:
                dict: The result of merging the provided facts with existing
                      local facts
        """
        changed = False

        facts_to_set = dict()

        if facts is not None:
            facts_to_set[self.role] = facts

        if openshift_env != {} and openshift_env != None:
            for fact, value in openshift_env.iteritems():
                oo_env_facts = dict()
                current_level = oo_env_facts
                keys = fact.split('_')[1:]
                if keys[0] != self.role:
                    continue
                for key in keys:
                    if key == keys[-1]:
                        if value is not None and value != "":
                            current_level[key] = value
                    elif key not in current_level:
                        current_level[key] = dict()
                        current_level = current_level[key]
                facts_to_set = merge_facts(orig=facts_to_set,
                                           new=oo_env_facts,
                                           additive_facts_to_overwrite=[],
                                           protected_facts_to_overwrite=[])

        local_facts = get_local_facts_from_file(self.filename)

        migrated_facts = migrate_local_facts(local_facts)

        new_local_facts = merge_facts(migrated_facts,
                                      facts_to_set,
                                      additive_facts_to_overwrite,
                                      protected_facts_to_overwrite)

        if 'docker' in new_local_facts:
            # remove duplicate and empty strings from registry lists
            for cat in  ['additional', 'blocked', 'insecure']:
                key = '{0}_registries'.format(cat)
                if key in new_local_facts['docker']:
                    val = new_local_facts['docker'][key]
                    if isinstance(val, basestring):
                        val = [x.strip() for x in val.split(',')]
                    new_local_facts['docker'][key] = list(set(val) - set(['']))

        for facts in new_local_facts.values():
            keys_to_delete = []
            if isinstance(facts, dict):
                for fact, value in facts.iteritems():
                    if value == "" or value is None:
                        keys_to_delete.append(fact)
                for key in keys_to_delete:
                    del facts[key]

        if new_local_facts != local_facts:
            self.validate_local_facts(new_local_facts)
            changed = True
            if not module.check_mode:
                save_local_facts(self.filename, new_local_facts)

        self.changed = changed
        return new_local_facts

    def validate_local_facts(self, facts=None):
        """ Validate local facts

            Args:
                facts (dict): local facts to validate
        """
        invalid_facts = dict()
        invalid_facts = self.validate_master_facts(facts, invalid_facts)
        if invalid_facts:
            msg = 'Invalid facts detected:\n'
            for key in invalid_facts.keys():
                msg += '{0}: {1}\n'.format(key, invalid_facts[key])
            module.fail_json(msg=msg,
                             changed=self.changed)

    # disabling pylint errors for line-too-long since we're dealing
    # with best effort reduction of error messages here.
    # disabling errors for too-many-branches since we require checking
    # many conditions.
    # pylint: disable=line-too-long, too-many-branches
    @staticmethod
    def validate_master_facts(facts, invalid_facts):
        """ Validate master facts

            Args:
                facts (dict): local facts to validate
                invalid_facts (dict): collected invalid_facts

            Returns:
                dict: Invalid facts
        """
        if 'master' in facts:
            # openshift.master.session_auth_secrets
            if 'session_auth_secrets' in facts['master']:
                session_auth_secrets = facts['master']['session_auth_secrets']
                if not issubclass(type(session_auth_secrets), list):
                    invalid_facts['session_auth_secrets'] = 'Expects session_auth_secrets is a list.'
                elif 'session_encryption_secrets' not in facts['master']:
                    invalid_facts['session_auth_secrets'] = ('openshift_master_session_encryption secrets must be set '
                                                             'if openshift_master_session_auth_secrets is provided.')
                elif len(session_auth_secrets) != len(facts['master']['session_encryption_secrets']):
                    invalid_facts['session_auth_secrets'] = ('openshift_master_session_auth_secrets and '
                                                             'openshift_master_session_encryption_secrets must be '
                                                             'equal length.')
                else:
                    for secret in session_auth_secrets:
                        if len(secret) < 32:
                            invalid_facts['session_auth_secrets'] = ('Invalid secret in session_auth_secrets. '
                                                                     'Secrets must be at least 32 characters in length.')
            # openshift.master.session_encryption_secrets
            if 'session_encryption_secrets' in facts['master']:
                session_encryption_secrets = facts['master']['session_encryption_secrets']
                if not issubclass(type(session_encryption_secrets), list):
                    invalid_facts['session_encryption_secrets'] = 'Expects session_encryption_secrets is a list.'
                elif 'session_auth_secrets' not in facts['master']:
                    invalid_facts['session_encryption_secrets'] = ('openshift_master_session_auth_secrets must be '
                                                                   'set if openshift_master_session_encryption_secrets '
                                                                   'is provided.')
                else:
                    for secret in session_encryption_secrets:
                        if len(secret) not in [16, 24, 32]:
                            invalid_facts['session_encryption_secrets'] = ('Invalid secret in session_encryption_secrets. '
                                                                           'Secrets must be 16, 24, or 32 characters in length.')
        return invalid_facts

def main():
    """ main """
    # disabling pylint errors for global-variable-undefined and invalid-name
    # for 'global module' usage, since it is required to use ansible_facts
    # pylint: disable=global-variable-undefined, invalid-name
    global module
    module = AnsibleModule(
        argument_spec=dict(
            role=dict(default='common', required=False,
                      choices=OpenShiftFacts.known_roles),
            local_facts=dict(default=None, type='dict', required=False),
            additive_facts_to_overwrite=dict(default=[], type='list', required=False),
            openshift_env=dict(default={}, type='dict', required=False),
            protected_facts_to_overwrite=dict(default=[], type='list', required=False),
        ),
        supports_check_mode=True,
        add_file_common_args=True,
    )

    role = module.params['role']
    local_facts = module.params['local_facts']
    additive_facts_to_overwrite = module.params['additive_facts_to_overwrite']
    openshift_env = module.params['openshift_env']
    protected_facts_to_overwrite = module.params['protected_facts_to_overwrite']

    fact_file = '/etc/ansible/facts.d/openshift.fact'

    openshift_facts = OpenShiftFacts(role,
                                     fact_file,
                                     local_facts,
                                     additive_facts_to_overwrite,
                                     openshift_env,
                                     protected_facts_to_overwrite)

    file_params = module.params.copy()
    file_params['path'] = fact_file
    file_args = module.load_file_common_arguments(file_params)
    changed = module.set_fs_attributes_if_different(file_args,
                                                    openshift_facts.changed)

    return module.exit_json(changed=changed,
                            ansible_facts=openshift_facts.facts)

# ignore pylint errors related to the module_utils import
# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import
# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.facts import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
