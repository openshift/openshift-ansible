#!/usr/bin/python
# pylint: disable=too-many-lines
# -*- coding: utf-8 -*-
# Reason: Disable pylint too-many-lines because we don't want to split up this file.
# Status: Permanently disabled to keep this module as self-contained as possible.

"""Ansible module for retrieving and setting openshift related facts"""

# pylint: disable=no-name-in-module, import-error, wrong-import-order
import copy
import errno
import json
import re
import io
import os
import yaml
import struct
import socket
from distutils.util import strtobool
from distutils.version import LooseVersion
from ansible.module_utils.six import string_types, text_type
from ansible.module_utils.six.moves import configparser

# ignore pylint errors related to the module_utils import
# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import
# import module snippets
from ansible.module_utils.basic import *  # noqa: F403
from ansible.module_utils.facts import *  # noqa: F403
from ansible.module_utils.urls import *  # noqa: F403
from ansible.module_utils.six import iteritems, itervalues
from ansible.module_utils.six.moves.urllib.parse import urlparse, urlunparse
from ansible.module_utils._text import to_native

HAVE_DBUS = False

try:
    from dbus import SystemBus, Interface
    from dbus.exceptions import DBusException
    HAVE_DBUS = True
except ImportError:
    pass

DOCUMENTATION = '''
---
module: openshift_facts
short_description: Cluster Facts
author: Jason DeTiberus
requirements: [ ]
'''
EXAMPLES = '''
'''


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
    # pylint: disable=consider-iterating-dictionary
    for role in params.keys():
        if role in facts:
            for param in params[role]:
                old_param = 'docker_' + param
                if old_param in facts[role]:
                    facts['docker'][param] = facts[role].pop(old_param)

    if 'node' in facts and 'portal_net' in facts['node']:
        facts['docker']['hosted_registry_network'] = facts['node'].pop('portal_net')

    # log_options was originally meant to be a comma separated string, but
    # we now prefer an actual list, with backward compatibility:
    if 'log_options' in facts['docker'] and \
            isinstance(facts['docker']['log_options'], string_types):
        facts['docker']['log_options'] = facts['docker']['log_options'].split(",")

    return facts


# TODO: We should add a generic migration function that takes source and destination
# paths and does the right thing rather than one function for common, one for node, etc.
def migrate_common_facts(facts):
    """ Migrate facts from various roles into common """
    params = {
        'node': ('portal_net'),
        'master': ('portal_net')
    }
    if 'common' not in facts:
        facts['common'] = {}
    # pylint: disable=consider-iterating-dictionary
    for role in params.keys():
        if role in facts:
            for param in params[role]:
                if param in facts[role]:
                    facts['common'][param] = facts[role].pop(param)
    return facts


def migrate_node_facts(facts):
    """ Migrate facts from various roles into node """
    params = {
        'common': ('dns_ip'),
    }
    if 'node' not in facts:
        facts['node'] = {}
    # pylint: disable=consider-iterating-dictionary
    for role in params.keys():
        if role in facts:
            for param in params[role]:
                if param in facts[role]:
                    facts['node'][param] = facts[role].pop(param)
    return facts


def migrate_hosted_facts(facts):
    """ Apply migrations for master facts """
    if 'master' in facts:
        if 'router_selector' in facts['master']:
            if 'hosted' not in facts:
                facts['hosted'] = {}
            if 'router' not in facts['hosted']:
                facts['hosted']['router'] = {}
            facts['hosted']['router']['selector'] = facts['master'].pop('router_selector')
        if 'registry_selector' in facts['master']:
            if 'hosted' not in facts:
                facts['hosted'] = {}
            if 'registry' not in facts['hosted']:
                facts['hosted']['registry'] = {}
            facts['hosted']['registry']['selector'] = facts['master'].pop('registry_selector')
    return facts


def migrate_admission_plugin_facts(facts):
    """ Apply migrations for admission plugin facts """
    if 'master' in facts:
        if 'kube_admission_plugin_config' in facts['master']:
            if 'admission_plugin_config' not in facts['master']:
                facts['master']['admission_plugin_config'] = dict()
            # Merge existing kube_admission_plugin_config with admission_plugin_config.
            facts['master']['admission_plugin_config'] = merge_facts(facts['master']['admission_plugin_config'],
                                                                     facts['master']['kube_admission_plugin_config'],
                                                                     additive_facts_to_overwrite=[],
                                                                     protected_facts_to_overwrite=[])
            # Remove kube_admission_plugin_config fact
            facts['master'].pop('kube_admission_plugin_config', None)
    return facts


def migrate_local_facts(facts):
    """ Apply migrations of local facts """
    migrated_facts = copy.deepcopy(facts)
    migrated_facts = migrate_docker_facts(migrated_facts)
    migrated_facts = migrate_common_facts(migrated_facts)
    migrated_facts = migrate_node_facts(migrated_facts)
    migrated_facts = migrate_hosted_facts(migrated_facts)
    migrated_facts = migrate_admission_plugin_facts(migrated_facts)
    return migrated_facts


def first_ip(network):
    """ Return the first IPv4 address in network

        Args:
            network (str): network in CIDR format
        Returns:
            str: first IPv4 address
    """
    atoi = lambda addr: struct.unpack("!I", socket.inet_aton(addr))[0]  # noqa: E731
    itoa = lambda addr: socket.inet_ntoa(struct.pack("!I", addr))  # noqa: E731

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
            hostname.endswith('localdomain')):
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
    ips = [i for i in hostnames if i is not None and isinstance(i, string_types) and re.match(ip_regex, i)]
    hosts = [i for i in hostnames if i is not None and i != '' and i not in ips]

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
    result, info = fetch_url(module, metadata_url, headers=headers)  # noqa: F405
    if info['status'] != 200:
        raise OpenShiftFactsMetadataUnavailableError("Metadata unavailable")
    if expect_json:
        return module.from_json(to_native(result.read()))  # noqa: F405
    else:
        return [to_native(line.strip()) for line in result.readlines()]


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
    # Split instance hostname from GCE metadata to use the short instance name
    facts['network']['hostname'] = metadata['instance']['hostname'].split('.')[0]

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
        for ips_var, int_var in iteritems(var_map):
            ips = interface.get(int_var)
            if isinstance(ips, string_types):
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

    for f_var, h_var, ip_var in [('hostname', 'hostname', 'local-ipv4'),
                                 ('public_hostname', 'public-hostname', 'public-ipv4')]:
        try:
            if socket.gethostbyname(metadata['ec2_compat'][h_var]) == metadata['ec2_compat'][ip_var]:
                facts['network'][f_var] = metadata['ec2_compat'][h_var]
            else:
                facts['network'][f_var] = metadata['ec2_compat'][ip_var]
        except socket.gaierror:
            facts['network'][f_var] = metadata['ec2_compat'][ip_var]

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

    if provider == 'gce':
        facts = normalize_gce_facts(metadata, facts)
    elif provider == 'aws':
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


def set_calico_facts_if_unset(facts):
    """ Set calico facts if not already present in facts dict
            dict: the facts dict updated with the calico facts if
            missing
        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with the calico
            facts if they were not already present

    """
    if 'common' in facts:
        if 'use_calico' not in facts['common']:
            use_calico = False
            facts['common']['use_calico'] = use_calico
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


def set_contiv_facts_if_unset(facts):
    """ Set contiv facts if not already present in facts dict
            dict: the facts dict updated with the contiv facts if
            missing
        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with the contiv
            facts if they were not already present

    """
    if 'common' in facts:
        if 'use_contiv' not in facts['common']:
            use_contiv = False
            facts['common']['use_contiv'] = use_contiv
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


def set_selectors(facts):
    """ Set selectors facts if not already present in facts dict
        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with the generated selectors
            facts if they were not already present

    """
    deployment_type = facts['common']['deployment_type']
    if deployment_type == 'online':
        selector = "type=infra"
    else:
        selector = "region=infra"

    if 'hosted' not in facts:
        facts['hosted'] = {}
    if 'router' not in facts['hosted']:
        facts['hosted']['router'] = {}
    if 'selector' not in facts['hosted']['router'] or facts['hosted']['router']['selector'] in [None, 'None']:
        facts['hosted']['router']['selector'] = selector
    if 'registry' not in facts['hosted']:
        facts['hosted']['registry'] = {}
    if 'selector' not in facts['hosted']['registry'] or facts['hosted']['registry']['selector'] in [None, 'None']:
        facts['hosted']['registry']['selector'] = selector
    if 'metrics' not in facts['hosted']:
        facts['hosted']['metrics'] = {}
    if 'selector' not in facts['hosted']['metrics'] or facts['hosted']['metrics']['selector'] in [None, 'None']:
        facts['hosted']['metrics']['selector'] = None
    if 'logging' not in facts['hosted']:
        facts['hosted']['logging'] = {}
    if 'selector' not in facts['hosted']['logging'] or facts['hosted']['logging']['selector'] in [None, 'None']:
        facts['hosted']['logging']['selector'] = None

    return facts


def set_dnsmasq_facts_if_unset(facts):
    """ Set dnsmasq facts if not already present in facts
    Args:
        facts (dict) existing facts
    Returns:
        facts (dict) updated facts with values set if not previously set
    """

    if 'common' in facts:
        if 'use_dnsmasq' not in facts['common']:
            facts['common']['use_dnsmasq'] = bool(safe_get_bool(facts['common']['version_gte_3_2_or_1_2']))
        if 'master' in facts and 'dns_port' not in facts['master']:
            if safe_get_bool(facts['common']['use_dnsmasq']):
                facts['master']['dns_port'] = 8053
            else:
                facts['master']['dns_port'] = 53

    return facts


def set_project_cfg_facts_if_unset(facts):
    """ Set Project Configuration facts if not already present in facts dict
            dict:
        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with the generated Project Configuration
            facts if they were not already present

    """

    config = {
        'default_node_selector': '',
        'project_request_message': '',
        'project_request_template': '',
        'mcs_allocator_range': 's0:/2',
        'mcs_labels_per_project': 5,
        'uid_allocator_range': '1000000000-1999999999/10000'
    }

    if 'master' in facts:
        for key, value in config.items():
            if key not in facts['master']:
                facts['master'][key] = value

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
    kube_svc_ip = first_ip(facts['common']['portal_net'])
    if 'common' in facts:
        all_hostnames.add(facts['common']['hostname'])
        all_hostnames.add(facts['common']['public_hostname'])
        all_hostnames.add(facts['common']['ip'])
        all_hostnames.add(facts['common']['public_ip'])
        facts['common']['kube_svc_ip'] = kube_svc_ip

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
            all_hostnames.add(kube_svc_ip)
            internal_hostnames.add(kube_svc_ip)

        facts['common']['all_hostnames'] = list(all_hostnames)
        facts['common']['internal_hostnames'] = list(internal_hostnames)

    return facts


def set_etcd_facts_if_unset(facts):
    """
    If using embedded etcd, loads the data directory from master-config.yaml.

    If using standalone etcd, loads ETCD_DATA_DIR from etcd.conf.

    If anything goes wrong parsing these, the fact will not be set.
    """
    if 'master' in facts and safe_get_bool(facts['master']['embedded_etcd']):
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
            ini_str = text_type('[root]\n' + open('/etc/etcd/etcd.conf', 'r').read(), 'utf-8')
            ini_fp = io.StringIO(ini_str)
            config = configparser.RawConfigParser()
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
    """ Set Facts that vary based on deployment_type. This currently
        includes common.service_type, master.registry_url, node.registry_url,
        node.storage_plugin_deps

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
        if 'service_type' not in facts['common']:
            service_type = 'atomic-openshift'
            if deployment_type == 'origin':
                service_type = 'origin'
            elif deployment_type in ['enterprise']:
                service_type = 'openshift'
            facts['common']['service_type'] = service_type

    if 'docker' in facts:
        deployment_type = facts['common']['deployment_type']
        if deployment_type in ['enterprise', 'atomic-enterprise', 'openshift-enterprise']:
            addtl_regs = facts['docker'].get('additional_registries', [])
            ent_reg = 'registry.access.redhat.com'
            if ent_reg not in addtl_regs:
                facts['docker']['additional_registries'] = addtl_regs + [ent_reg]

    for role in ('master', 'node'):
        if role in facts:
            deployment_type = facts['common']['deployment_type']
            if 'registry_url' not in facts[role]:
                registry_url = 'openshift/origin-${component}:${version}'
                if deployment_type in ['enterprise', 'online', 'openshift-enterprise']:
                    registry_url = 'openshift3/ose-${component}:${version}'
                elif deployment_type == 'atomic-enterprise':
                    registry_url = 'aep3_beta/aep-${component}:${version}'
                facts[role]['registry_url'] = registry_url

    if 'master' in facts:
        deployment_type = facts['common']['deployment_type']
        openshift_features = ['Builder', 'S2IBuilder', 'WebConsole']
        if 'disabled_features' in facts['master']:
            if deployment_type == 'atomic-enterprise':
                curr_disabled_features = set(facts['master']['disabled_features'])
                facts['master']['disabled_features'] = list(curr_disabled_features.union(openshift_features))
        else:
            if facts['common']['deployment_subtype'] == 'registry':
                facts['master']['disabled_features'] = openshift_features

    if 'node' in facts:
        deployment_type = facts['common']['deployment_type']
        if 'storage_plugin_deps' not in facts['node']:
            if deployment_type in ['openshift-enterprise', 'atomic-enterprise', 'origin']:
                facts['node']['storage_plugin_deps'] = ['ceph', 'glusterfs', 'iscsi']
            else:
                facts['node']['storage_plugin_deps'] = []

    return facts


# pylint: disable=too-many-statements
def set_version_facts_if_unset(facts):
    """ Set version facts. This currently includes common.version and
        common.version_gte_3_1_or_1_1.

        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with version facts.
    """
    if 'common' in facts:
        deployment_type = facts['common']['deployment_type']
        openshift_version = get_openshift_version(facts)
        if openshift_version and openshift_version != "latest":
            version = LooseVersion(openshift_version)
            facts['common']['version'] = openshift_version
            facts['common']['short_version'] = '.'.join([str(x) for x in version.version[0:2]])
            if deployment_type == 'origin':
                version_gte_3_1_or_1_1 = version >= LooseVersion('1.1.0')
                version_gte_3_1_1_or_1_1_1 = version >= LooseVersion('1.1.1')
                version_gte_3_2_or_1_2 = version >= LooseVersion('1.2.0')
                version_gte_3_3_or_1_3 = version >= LooseVersion('1.3.0')
                version_gte_3_4_or_1_4 = version >= LooseVersion('1.4.0')
                version_gte_3_5_or_1_5 = version >= LooseVersion('1.5.0')
                version_gte_3_6 = version >= LooseVersion('3.6.0')
            else:
                version_gte_3_1_or_1_1 = version >= LooseVersion('3.0.2.905')
                version_gte_3_1_1_or_1_1_1 = version >= LooseVersion('3.1.1')
                version_gte_3_2_or_1_2 = version >= LooseVersion('3.1.1.901')
                version_gte_3_3_or_1_3 = version >= LooseVersion('3.3.0')
                version_gte_3_4_or_1_4 = version >= LooseVersion('3.4.0')
                version_gte_3_5_or_1_5 = version >= LooseVersion('3.5.0')
                version_gte_3_6 = version >= LooseVersion('3.6.0')
        else:
            # 'Latest' version is set to True, 'Next' versions set to False
            version_gte_3_1_or_1_1 = True
            version_gte_3_1_1_or_1_1_1 = True
            version_gte_3_2_or_1_2 = True
            version_gte_3_3_or_1_3 = True
            version_gte_3_4_or_1_4 = True
            version_gte_3_5_or_1_5 = True
            version_gte_3_6 = True
        facts['common']['version_gte_3_1_or_1_1'] = version_gte_3_1_or_1_1
        facts['common']['version_gte_3_1_1_or_1_1_1'] = version_gte_3_1_1_or_1_1_1
        facts['common']['version_gte_3_2_or_1_2'] = version_gte_3_2_or_1_2
        facts['common']['version_gte_3_3_or_1_3'] = version_gte_3_3_or_1_3
        facts['common']['version_gte_3_4_or_1_4'] = version_gte_3_4_or_1_4
        facts['common']['version_gte_3_5_or_1_5'] = version_gte_3_5_or_1_5
        facts['common']['version_gte_3_6'] = version_gte_3_6

        if version_gte_3_6:
            examples_content_version = 'v3.6'
        elif version_gte_3_5_or_1_5:
            examples_content_version = 'v1.5'
        elif version_gte_3_4_or_1_4:
            examples_content_version = 'v1.4'
        elif version_gte_3_3_or_1_3:
            examples_content_version = 'v1.3'
        elif version_gte_3_2_or_1_2:
            examples_content_version = 'v1.2'
        elif version_gte_3_1_or_1_1:
            examples_content_version = 'v1.1'
        else:
            examples_content_version = 'v1.0'

        facts['common']['examples_content_version'] = examples_content_version

    return facts


def set_manageiq_facts_if_unset(facts):
    """ Set manageiq facts. This currently includes common.use_manageiq.

        Args:
            facts (dict): existing facts
        Returns:
            dict: the facts dict updated with version facts.
        Raises:
            OpenShiftFactsInternalError:
    """
    if 'common' not in facts:
        if 'version_gte_3_1_or_1_1' not in facts['common']:
            raise OpenShiftFactsInternalError(
                "Invalid invocation: The required facts are not set"
            )
    if 'use_manageiq' not in facts['common']:
        facts['common']['use_manageiq'] = facts['common']['version_gte_3_1_or_1_1']

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
    # pylint: disable=too-many-branches
    if 'common' in facts:
        use_sdn = facts['common']['use_openshift_sdn']
        if not (use_sdn == '' or isinstance(use_sdn, bool)):
            use_sdn = safe_get_bool(use_sdn)
            facts['common']['use_openshift_sdn'] = use_sdn
        if 'sdn_network_plugin_name' not in facts['common']:
            plugin = 'redhat/openshift-ovs-subnet' if use_sdn else ''
            facts['common']['sdn_network_plugin_name'] = plugin

    if 'master' in facts:
        # set defaults for sdn_cluster_network_cidr and sdn_host_subnet_length
        # these might be overridden if they exist in the master config file
        sdn_cluster_network_cidr = '10.128.0.0/14'
        sdn_host_subnet_length = '9'

        master_cfg_path = os.path.join(facts['common']['config_base'],
                                       'master/master-config.yaml')
        if os.path.isfile(master_cfg_path):
            with open(master_cfg_path, 'r') as master_cfg_f:
                config = yaml.safe_load(master_cfg_f.read())

            if 'networkConfig' in config:
                if 'clusterNetworkCIDR' in config['networkConfig']:
                    sdn_cluster_network_cidr = \
                        config['networkConfig']['clusterNetworkCIDR']
                if 'hostSubnetLength' in config['networkConfig']:
                    sdn_host_subnet_length = \
                        config['networkConfig']['hostSubnetLength']

        if 'sdn_cluster_network_cidr' not in facts['master']:
            facts['master']['sdn_cluster_network_cidr'] = sdn_cluster_network_cidr
        if 'sdn_host_subnet_length' not in facts['master']:
            facts['master']['sdn_host_subnet_length'] = sdn_host_subnet_length

    if 'node' in facts and 'sdn_mtu' not in facts['node']:
        node_ip = facts['common']['ip']

        # default MTU if interface MTU cannot be detected
        facts['node']['sdn_mtu'] = '1450'

        for val in itervalues(system_facts):
            if isinstance(val, dict) and 'mtu' in val:
                mtu = val['mtu']

                if 'ipv4' in val and val['ipv4'].get('address') == node_ip:
                    facts['node']['sdn_mtu'] = str(mtu - 50)

    return facts


def set_nodename(facts):
    """ set nodename """
    if 'node' in facts and 'common' in facts:
        if 'cloudprovider' in facts and facts['cloudprovider']['kind'] == 'gce':
            facts['node']['nodename'] = facts['provider']['metadata']['instance']['hostname'].split('.')[0]

        # TODO: The openstack cloudprovider nodename setting was too opinionaed.
        #       It needs to be generalized before it can be enabled again.
        # elif 'cloudprovider' in facts and facts['cloudprovider']['kind'] == 'openstack':
        #     facts['node']['nodename'] = facts['provider']['metadata']['hostname'].replace('.novalocal', '')
        else:
            facts['node']['nodename'] = facts['common']['hostname'].lower()
    return facts


def migrate_oauth_template_facts(facts):
    """
    Migrate an old oauth template fact to a newer format if it's present.

    The legacy 'oauth_template' fact was just a filename, and assumed you were
    setting the 'login' template.

    The new pluralized 'oauth_templates' fact is a dict mapping the template
    name to a filename.

    Simplify the code after this by merging the old fact into the new.
    """
    if 'master' in facts and 'oauth_template' in facts['master']:
        if 'oauth_templates' not in facts['master']:
            facts['master']['oauth_templates'] = {"login": facts['master']['oauth_template']}
        elif 'login' not in facts['master']['oauth_templates']:
            facts['master']['oauth_templates']['login'] = facts['master']['oauth_template']
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
    try:
        url = urlparse.urlunparse((scheme, netloc, path, '', '', ''))
    except AttributeError:
        # pylint: disable=undefined-variable
        url = urlunparse((scheme, netloc, path, '', '', ''))
    return url


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
        if os.path.isfile('/usr/bin/openshift') and os.path.isfile(kubeconfig_path):
            try:
                _, output, _ = module.run_command(  # noqa: F405
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


def build_kubelet_args(facts):
    """Build node kubelet_args

In the node-config.yaml file, kubeletArgument sub-keys have their
values provided as a list. Hence the gratuitous use of ['foo'] below.
    """
    cloud_cfg_path = os.path.join(
        facts['common']['config_base'],
        'cloudprovider')

    # We only have to do this stuff on hosts that are nodes
    if 'node' in facts:
        # Any changes to the kubeletArguments parameter are stored
        # here first.
        kubelet_args = {}

        if 'cloudprovider' in facts:
            # EVERY cloud is special <3
            if 'kind' in facts['cloudprovider']:
                if facts['cloudprovider']['kind'] == 'aws':
                    kubelet_args['cloud-provider'] = ['aws']
                    kubelet_args['cloud-config'] = [cloud_cfg_path + '/aws.conf']
                if facts['cloudprovider']['kind'] == 'openstack':
                    kubelet_args['cloud-provider'] = ['openstack']
                    kubelet_args['cloud-config'] = [cloud_cfg_path + '/openstack.conf']
                if facts['cloudprovider']['kind'] == 'gce':
                    kubelet_args['cloud-provider'] = ['gce']
                    kubelet_args['cloud-config'] = [cloud_cfg_path + '/gce.conf']

        # Automatically add node-labels to the kubeletArguments
        # parameter. See BZ1359848 for additional details.
        #
        # Ref: https://bugzilla.redhat.com/show_bug.cgi?id=1359848
        if 'labels' in facts['node'] and isinstance(facts['node']['labels'], dict):
            # tl;dr: os_node_labels="{'foo': 'bar', 'a': 'b'}" turns
            # into ['foo=bar', 'a=b']
            #
            # On the openshift_node_labels inventory variable we loop
            # over each key-value tuple (from .items()) and join the
            # key to the value with an '=' character, this produces a
            # list.
            #
            # map() seems to be returning an itertools.imap object
            # instead of a list. We cast it to a list ourselves.
            # pylint: disable=unnecessary-lambda
            labels_str = list(map(lambda x: '='.join(x), facts['node']['labels'].items()))
            if labels_str != '':
                kubelet_args['node-labels'] = labels_str

        # If we've added items to the kubelet_args dict then we need
        # to merge the new items back into the main facts object.
        if kubelet_args != {}:
            facts = merge_facts({'node': {'kubelet_args': kubelet_args}}, facts, [], [])
    return facts


def build_controller_args(facts):
    """ Build master controller_args """
    cloud_cfg_path = os.path.join(facts['common']['config_base'],
                                  'cloudprovider')
    if 'master' in facts:
        controller_args = {}
        if 'cloudprovider' in facts:
            if 'kind' in facts['cloudprovider']:
                if facts['cloudprovider']['kind'] == 'aws':
                    controller_args['cloud-provider'] = ['aws']
                    controller_args['cloud-config'] = [cloud_cfg_path + '/aws.conf']
                if facts['cloudprovider']['kind'] == 'openstack':
                    controller_args['cloud-provider'] = ['openstack']
                    controller_args['cloud-config'] = [cloud_cfg_path + '/openstack.conf']
                if facts['cloudprovider']['kind'] == 'gce':
                    controller_args['cloud-provider'] = ['gce']
                    controller_args['cloud-config'] = [cloud_cfg_path + '/gce.conf']
        if controller_args != {}:
            facts = merge_facts({'master': {'controller_args': controller_args}}, facts, [], [])
    return facts


def build_api_server_args(facts):
    """ Build master api_server_args """
    cloud_cfg_path = os.path.join(facts['common']['config_base'],
                                  'cloudprovider')
    if 'master' in facts:
        api_server_args = {}
        if 'cloudprovider' in facts:
            if 'kind' in facts['cloudprovider']:
                if facts['cloudprovider']['kind'] == 'aws':
                    api_server_args['cloud-provider'] = ['aws']
                    api_server_args['cloud-config'] = [cloud_cfg_path + '/aws.conf']
                if facts['cloudprovider']['kind'] == 'openstack':
                    api_server_args['cloud-provider'] = ['openstack']
                    api_server_args['cloud-config'] = [cloud_cfg_path + '/openstack.conf']
                if facts['cloudprovider']['kind'] == 'gce':
                    api_server_args['cloud-provider'] = ['gce']
                    api_server_args['cloud-config'] = [cloud_cfg_path + '/gce.conf']
        if api_server_args != {}:
            facts = merge_facts({'master': {'api_server_args': api_server_args}}, facts, [], [])
    return facts


def is_service_running(service):
    """ Queries systemd through dbus to see if the service is running """
    service_running = False
    try:
        bus = SystemBus()
        systemd = bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
        manager = Interface(systemd, dbus_interface='org.freedesktop.systemd1.Manager')
        service_unit = service if service.endswith('.service') else manager.GetUnit('{0}.service'.format(service))
        service_proxy = bus.get_object('org.freedesktop.systemd1', str(service_unit))
        service_properties = Interface(service_proxy, dbus_interface='org.freedesktop.DBus.Properties')
        service_load_state = service_properties.Get('org.freedesktop.systemd1.Unit', 'LoadState')
        service_active_state = service_properties.Get('org.freedesktop.systemd1.Unit', 'ActiveState')
        if service_load_state == 'loaded' and service_active_state == 'active':
            service_running = True
    except DBusException:
        # TODO: do not swallow exception, as it may be hiding useful debugging
        # information.
        pass

    return service_running


def rpm_rebuilddb():
    """
    Runs rpm --rebuilddb to ensure the db is in good shape.
    """
    module.run_command(['/usr/bin/rpm', '--rebuilddb'])  # noqa: F405


def get_version_output(binary, version_cmd):
    """ runs and returns the version output for a command """
    cmd = []
    for item in (binary, version_cmd):
        if isinstance(item, list):
            cmd.extend(item)
        else:
            cmd.append(item)

    if os.path.isfile(cmd[0]):
        _, output, _ = module.run_command(cmd)  # noqa: F405
    return output


def get_docker_version_info():
    """ Parses and returns the docker version info """
    result = None
    if is_service_running('docker') or is_service_running('container-engine'):
        version_info = yaml.safe_load(get_version_output('/usr/bin/docker', 'version'))
        if 'Server' in version_info:
            result = {
                'api_version': version_info['Server']['API version'],
                'version': version_info['Server']['Version']
            }
    return result


def get_hosted_registry_insecure():
    """ Parses OPTIONS from /etc/sysconfig/docker to determine if the
        registry is currently insecure.
    """
    hosted_registry_insecure = None
    if os.path.exists('/etc/sysconfig/docker'):
        try:
            ini_str = text_type('[root]\n' + open('/etc/sysconfig/docker', 'r').read(), 'utf-8')
            ini_fp = io.StringIO(ini_str)
            config = configparser.RawConfigParser()
            config.readfp(ini_fp)
            options = config.get('root', 'OPTIONS')
            if 'insecure-registry' in options:
                hosted_registry_insecure = True
        except Exception:  # pylint: disable=broad-except
            pass
    return hosted_registry_insecure


def get_openshift_version(facts):
    """ Get current version of openshift on the host.

        Checks a variety of ways ranging from fastest to slowest.

        Args:
            facts (dict): existing facts
            optional cli_image for pulling the version number

        Returns:
            version: the current openshift version
    """
    version = None

    # No need to run this method repeatedly on a system if we already know the
    # version
    # TODO: We need a way to force reload this after upgrading bits.
    if 'common' in facts:
        if 'version' in facts['common'] and facts['common']['version'] is not None:
            return chomp_commit_offset(facts['common']['version'])

    if os.path.isfile('/usr/bin/openshift'):
        _, output, _ = module.run_command(['/usr/bin/openshift', 'version'])  # noqa: F405
        version = parse_openshift_version(output)
    elif 'common' in facts and 'is_containerized' in facts['common']:
        version = get_container_openshift_version(facts)

    # Handle containerized masters that have not yet been configured as a node.
    # This can be very slow and may get re-run multiple times, so we only use this
    # if other methods failed to find a version.
    if not version and os.path.isfile('/usr/local/bin/openshift'):
        _, output, _ = module.run_command(['/usr/local/bin/openshift', 'version'])  # noqa: F405
        version = parse_openshift_version(output)

    return chomp_commit_offset(version)


def chomp_commit_offset(version):
    """Chomp any "+git.foo" commit offset string from the given `version`
    and return the modified version string.

Ex:
- chomp_commit_offset(None)                 => None
- chomp_commit_offset(1337)                 => "1337"
- chomp_commit_offset("v3.4.0.15+git.derp") => "v3.4.0.15"
- chomp_commit_offset("v3.4.0.15")          => "v3.4.0.15"
- chomp_commit_offset("v1.3.0+52492b4")     => "v1.3.0"
    """
    if version is None:
        return version
    else:
        # Stringify, just in case it's a Number type. Split by '+' and
        # return the first split. No concerns about strings without a
        # '+', .split() returns an array of the original string.
        return str(version).split('+')[0]


def get_container_openshift_version(facts):
    """
    If containerized, see if we can determine the installed version via the
    systemd environment files.
    """
    for filename in ['/etc/sysconfig/%s-master', '/etc/sysconfig/%s-node']:
        env_path = filename % facts['common']['service_type']
        if not os.path.exists(env_path):
            continue

        with open(env_path) as env_file:
            for line in env_file:
                if line.startswith("IMAGE_VERSION="):
                    tag = line[len("IMAGE_VERSION="):].strip()
                    # Remove leading "v" and any trailing release info, we just want
                    # a version number here:
                    no_v_version = tag[1:] if tag[0] == 'v' else tag
                    version = no_v_version.split("-")[0]
                    return version
    return None


def parse_openshift_version(output):
    """ Apply provider facts to supplied facts dict

        Args:
            string: output of 'openshift version'
        Returns:
            string: the version number
    """
    versions = dict(e.split(' v') for e in output.splitlines() if ' v' in e)
    ver = versions.get('openshift', '')
    # Remove trailing build number and commit hash from older versions, we need to return a straight
    # w.x.y.z version here for use as openshift_version throughout the playbooks/roles. (i.e. 3.1.1.6-64-g80b61da)
    ver = ver.split('-')[0]
    return ver


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
            facts['common'][h_var]
        )

    facts['provider'] = provider_facts
    return facts


# Disabling pylint too many branches. This function needs refactored
# but is a very core part of openshift_facts.
# pylint: disable=too-many-branches, too-many-nested-blocks
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
    protected_facts = ['ha']

    # Facts we do not ever want to merge. These originate in inventory variables
    # and contain JSON dicts. We don't ever want to trigger a merge
    # here, just completely overwrite with the new if they are present there.
    inventory_json_facts = ['admission_plugin_config',
                            'kube_admission_plugin_config',
                            'image_policy_config',
                            "builddefaults",
                            "buildoverrides"]

    facts = dict()
    for key, value in iteritems(orig):
        # Key exists in both old and new facts.
        if key in new:
            if key in inventory_json_facts:
                # Watchout for JSON facts that sometimes load as strings.
                # (can happen if the JSON contains a boolean)
                if isinstance(new[key], string_types):
                    facts[key] = yaml.safe_load(new[key])
                else:
                    facts[key] = copy.deepcopy(new[key])
            # Continue to recurse if old and new fact is a dictionary.
            elif isinstance(value, dict) and isinstance(new[key], dict):
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
                # ha (bool) can not change unless it has been passed
                # as a protected fact to overwrite.
                if key == 'ha':
                    if safe_get_bool(value) != safe_get_bool(new[key]):
                        # pylint: disable=line-too-long
                        module.fail_json(msg='openshift_facts received a different value for openshift.master.ha')  # noqa: F405
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
        # Watchout for JSON facts that sometimes load as strings.
        # (can happen if the JSON contains a boolean)
        if key in inventory_json_facts and isinstance(new[key], string_types):
            facts[key] = yaml.safe_load(new[key])
        else:
            facts[key] = copy.deepcopy(new[key])
    return facts


def save_local_facts(filename, facts):
    """ Save local facts

        Args:
            filename (str): local facts file
            facts (dict): facts to set
    """
    try:
        fact_dir = os.path.dirname(filename)
        try:
            os.makedirs(fact_dir)  # try to make the directory
        except OSError as exception:
            if exception.errno != errno.EEXIST:  # but it is okay if it is already there
                raise  # pass any other exceptions up the chain
        with open(filename, 'w') as fact_file:
            fact_file.write(module.jsonify(facts))  # noqa: F405
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
        ini_facts = configparser.SafeConfigParser()
        ini_facts.read(filename)
        for section in ini_facts.sections():
            local_facts[section] = dict()
            for key, value in ini_facts.items(section):
                local_facts[section][key] = value

    except (configparser.MissingSectionHeaderError,
            configparser.ParsingError):
        try:
            with open(filename, 'r') as facts_file:
                local_facts = json.load(facts_file)
        except (ValueError, IOError):
            pass

    return local_facts


def sort_unique(alist):
    """ Sorts and de-dupes a list

        Args:
            list: a list
        Returns:
            list: a sorted de-duped list
    """

    alist.sort()
    out = list()
    for i in alist:
        if i not in out:
            out.append(i)

    return out


def safe_get_bool(fact):
    """ Get a boolean fact safely.

        Args:
            facts: fact to convert
        Returns:
            bool: given fact as a bool
    """
    return bool(strtobool(str(fact)))


def set_proxy_facts(facts):
    """ Set global proxy facts

        Args:
            facts(dict): existing facts
        Returns:
            facts(dict): Updated facts with missing values
    """
    if 'common' in facts:
        common = facts['common']
        if 'http_proxy' in common or 'https_proxy' in common:
            if 'no_proxy' in common and isinstance(common['no_proxy'], string_types):
                common['no_proxy'] = common['no_proxy'].split(",")
            elif 'no_proxy' not in common:
                common['no_proxy'] = []
            if 'generate_no_proxy_hosts' in common and safe_get_bool(common['generate_no_proxy_hosts']):
                if 'no_proxy_internal_hostnames' in common:
                    common['no_proxy'].extend(common['no_proxy_internal_hostnames'].split(','))
            # We always add local dns domain and ourselves no matter what
            common['no_proxy'].append('.' + common['dns_domain'])
            common['no_proxy'].append(common['hostname'])
            common['no_proxy'] = ','.join(sort_unique(common['no_proxy']))
        facts['common'] = common
    return facts


def set_builddefaults_facts(facts):
    """ Set build defaults including setting proxy values from http_proxy, https_proxy,
        no_proxy to the more specific builddefaults and builddefaults_git vars.
           1. http_proxy, https_proxy, no_proxy
           2. builddefaults_*
           3. builddefaults_git_*

        Args:
            facts(dict): existing facts
        Returns:
            facts(dict): Updated facts with missing values
    """

    if 'builddefaults' in facts:
        builddefaults = facts['builddefaults']
        common = facts['common']
        # Copy values from common to builddefaults
        if 'http_proxy' not in builddefaults and 'http_proxy' in common:
            builddefaults['http_proxy'] = common['http_proxy']
        if 'https_proxy' not in builddefaults and 'https_proxy' in common:
            builddefaults['https_proxy'] = common['https_proxy']
        if 'no_proxy' not in builddefaults and 'no_proxy' in common:
            builddefaults['no_proxy'] = common['no_proxy']

        # Create git specific facts from generic values, if git specific values are
        # not defined.
        if 'git_http_proxy' not in builddefaults and 'http_proxy' in builddefaults:
            builddefaults['git_http_proxy'] = builddefaults['http_proxy']
        if 'git_https_proxy' not in builddefaults and 'https_proxy' in builddefaults:
            builddefaults['git_https_proxy'] = builddefaults['https_proxy']
        if 'git_no_proxy' not in builddefaults and 'no_proxy' in builddefaults:
            builddefaults['git_no_proxy'] = builddefaults['no_proxy']
        # If we're actually defining a builddefaults config then create admission_plugin_config
        # then merge builddefaults[config] structure into admission_plugin_config
        if 'config' in builddefaults:
            if 'admission_plugin_config' not in facts['master']:
                facts['master']['admission_plugin_config'] = dict()
            facts['master']['admission_plugin_config'].update(builddefaults['config'])
            # if the user didn't actually provide proxy values, delete the proxy env variable defaults.
            delete_empty_keys(facts['master']['admission_plugin_config']['BuildDefaults']['configuration']['env'])

    return facts


def delete_empty_keys(keylist):
    """ Delete dictionary elements from keylist where "value" is empty.

        Args:
          keylist(list): A list of builddefault configuration envs.

        Returns:
          none

        Example:
          keylist = [{'name': 'HTTP_PROXY', 'value': 'http://file.rdu.redhat.com:3128'},
                     {'name': 'HTTPS_PROXY', 'value': 'http://file.rdu.redhat.com:3128'},
                     {'name': 'NO_PROXY', 'value': ''}]

          After calling delete_empty_keys the provided list is modified to become:

                    [{'name': 'HTTP_PROXY', 'value': 'http://file.rdu.redhat.com:3128'},
                     {'name': 'HTTPS_PROXY', 'value': 'http://file.rdu.redhat.com:3128'}]
    """
    count = 0
    for i in range(0, len(keylist)):
        if len(keylist[i - count]['value']) == 0:
            del keylist[i - count]
            count += 1


def set_buildoverrides_facts(facts):
    """ Set build overrides

        Args:
            facts(dict): existing facts
        Returns:
            facts(dict): Updated facts with missing values
    """
    if 'buildoverrides' in facts:
        buildoverrides = facts['buildoverrides']
        # If we're actually defining a buildoverrides config then create admission_plugin_config
        # then merge buildoverrides[config] structure into admission_plugin_config
        if 'config' in buildoverrides:
            if 'admission_plugin_config' not in facts['master']:
                facts['master']['admission_plugin_config'] = dict()
            facts['master']['admission_plugin_config'].update(buildoverrides['config'])

    return facts


# pylint: disable=too-many-statements
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
        pod_image = 'openshift3/ose-pod'
        router_image = 'openshift3/ose-haproxy-router'
        registry_image = 'openshift3/ose-docker-registry'
        deployer_image = 'openshift3/ose-deployer'
    elif deployment_type == 'atomic-enterprise':
        master_image = 'aep3_beta/aep'
        cli_image = master_image
        node_image = 'aep3_beta/node'
        ovs_image = 'aep3_beta/openvswitch'
        etcd_image = 'registry.access.redhat.com/rhel7/etcd'
        pod_image = 'aep3_beta/aep-pod'
        router_image = 'aep3_beta/aep-haproxy-router'
        registry_image = 'aep3_beta/aep-docker-registry'
        deployer_image = 'aep3_beta/aep-deployer'
    else:
        master_image = 'openshift/origin'
        cli_image = master_image
        node_image = 'openshift/node'
        ovs_image = 'openshift/openvswitch'
        etcd_image = 'registry.access.redhat.com/rhel7/etcd'
        pod_image = 'openshift/origin-pod'
        router_image = 'openshift/origin-haproxy-router'
        registry_image = 'openshift/origin-docker-registry'
        deployer_image = 'openshift/origin-deployer'

    facts['common']['is_atomic'] = os.path.isfile('/run/ostree-booted')
    # If openshift_docker_use_system_container is set and is True ....
    if 'use_system_container' in list(facts['docker'].keys()):
        if facts['docker']['use_system_container']:
            # ... set the service name to container-engine
            facts['docker']['service_name'] = 'container-engine'

    if 'is_containerized' not in facts['common']:
        facts['common']['is_containerized'] = facts['common']['is_atomic']
    if 'cli_image' not in facts['common']:
        facts['common']['cli_image'] = cli_image
    if 'pod_image' not in facts['common']:
        facts['common']['pod_image'] = pod_image
    if 'router_image' not in facts['common']:
        facts['common']['router_image'] = router_image
    if 'registry_image' not in facts['common']:
        facts['common']['registry_image'] = registry_image
    if 'deployer_image' not in facts['common']:
        facts['common']['deployer_image'] = deployer_image
    if 'etcd' in facts and 'etcd_image' not in facts['etcd']:
        facts['etcd']['etcd_image'] = etcd_image
    if 'master' in facts and 'master_image' not in facts['master']:
        facts['master']['master_image'] = master_image
        facts['master']['master_system_image'] = master_image
    if 'node' in facts:
        if 'node_image' not in facts['node']:
            facts['node']['node_image'] = node_image
            facts['node']['node_system_image'] = node_image
        if 'ovs_image' not in facts['node']:
            facts['node']['ovs_image'] = ovs_image
            facts['node']['ovs_system_image'] = ovs_image

    if safe_get_bool(facts['common']['is_containerized']):
        facts['common']['admin_binary'] = '/usr/local/bin/oadm'
        facts['common']['client_binary'] = '/usr/local/bin/oc'

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
            exit_code, _, _ = module.run_command(['rpm', '-q', rpm])  # noqa: F405
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
    known_roles = ['builddefaults',
                   'buildoverrides',
                   'clock',
                   'cloudprovider',
                   'common',
                   'docker',
                   'etcd',
                   'hosted',
                   'master',
                   'node']

    # Disabling too-many-arguments, this should be cleaned up as a TODO item.
    # pylint: disable=too-many-arguments,no-value-for-parameter
    def __init__(self, role, filename, local_facts,
                 additive_facts_to_overwrite=None,
                 openshift_env=None,
                 openshift_env_structures=None,
                 protected_facts_to_overwrite=None):
        self.changed = False
        self.filename = filename
        if role not in self.known_roles:
            raise OpenShiftFactsUnsupportedRoleError(
                "Role %s is not supported by this module" % role
            )
        self.role = role

        # Collect system facts and preface each fact with 'ansible_'.
        try:
            # pylint: disable=too-many-function-args,invalid-name
            self.system_facts = ansible_facts(module, ['hardware', 'network', 'virtual', 'facter'])  # noqa: F405
            additional_facts = {}
            for (k, v) in self.system_facts.items():
                additional_facts["ansible_%s" % k.replace('-', '_')] = v
            self.system_facts.update(additional_facts)
        except UnboundLocalError:
            # ansible-2.2,2.3
            self.system_facts = get_all_facts(module)['ansible_facts']  # noqa: F405

        self.facts = self.generate_facts(local_facts,
                                         additive_facts_to_overwrite,
                                         openshift_env,
                                         openshift_env_structures,
                                         protected_facts_to_overwrite)

    def generate_facts(self,
                       local_facts,
                       additive_facts_to_overwrite,
                       openshift_env,
                       openshift_env_structures,
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
                                            openshift_env_structures,
                                            protected_facts_to_overwrite)
        roles = local_facts.keys()

        if 'common' in local_facts and 'deployment_type' in local_facts['common']:
            deployment_type = local_facts['common']['deployment_type']
        else:
            deployment_type = 'origin'

        if 'common' in local_facts and 'deployment_subtype' in local_facts['common']:
            deployment_subtype = local_facts['common']['deployment_subtype']
        else:
            deployment_subtype = 'basic'

        defaults = self.get_defaults(roles, deployment_type, deployment_subtype)
        provider_facts = self.init_provider_facts()
        facts = apply_provider_facts(defaults, provider_facts)
        facts = merge_facts(facts,
                            local_facts,
                            additive_facts_to_overwrite,
                            protected_facts_to_overwrite)
        facts = migrate_oauth_template_facts(facts)
        facts['current_config'] = get_current_config(facts)
        facts = set_url_facts_if_unset(facts)
        facts = set_project_cfg_facts_if_unset(facts)
        facts = set_flannel_facts_if_unset(facts)
        facts = set_calico_facts_if_unset(facts)
        facts = set_nuage_facts_if_unset(facts)
        facts = set_contiv_facts_if_unset(facts)
        facts = set_node_schedulability(facts)
        facts = set_selectors(facts)
        facts = set_identity_providers_if_unset(facts)
        facts = set_deployment_facts_if_unset(facts)
        facts = set_sdn_facts_if_unset(facts, self.system_facts)
        facts = set_container_facts_if_unset(facts)
        facts = build_kubelet_args(facts)
        facts = build_controller_args(facts)
        facts = build_api_server_args(facts)
        facts = set_version_facts_if_unset(facts)
        facts = set_dnsmasq_facts_if_unset(facts)
        facts = set_manageiq_facts_if_unset(facts)
        facts = set_aggregate_facts(facts)
        facts = set_etcd_facts_if_unset(facts)
        facts = set_proxy_facts(facts)
        facts = set_builddefaults_facts(facts)
        facts = set_buildoverrides_facts(facts)
        if not safe_get_bool(facts['common']['is_containerized']):
            facts = set_installed_variant_rpm_facts(facts)
        facts = set_nodename(facts)
        return dict(openshift=facts)

    def get_defaults(self, roles, deployment_type, deployment_subtype):
        """ Get default fact values

            Args:
                roles (list): list of roles for this host

            Returns:
                dict: The generated default facts
        """
        defaults = {}
        ip_addr = self.system_facts['ansible_default_ipv4']['address']
        exit_code, output, _ = module.run_command(['hostname', '-f'])  # noqa: F405
        hostname_f = output.strip() if exit_code == 0 else ''
        hostname_values = [hostname_f, self.system_facts['ansible_nodename'],
                           self.system_facts['ansible_fqdn']]
        hostname = choose_hostname(hostname_values, ip_addr)

        defaults['common'] = dict(use_openshift_sdn=True, ip=ip_addr,
                                  public_ip=ip_addr,
                                  deployment_type=deployment_type,
                                  deployment_subtype=deployment_subtype,
                                  hostname=hostname,
                                  public_hostname=hostname,
                                  portal_net='172.30.0.0/16',
                                  client_binary='oc', admin_binary='oadm',
                                  dns_domain='cluster.local',
                                  install_examples=True,
                                  debug_level=2,
                                  config_base='/etc/origin',
                                  data_dir='/var/lib/origin')

        if 'master' in roles:
            defaults['master'] = dict(api_use_ssl=True, api_port='8443',
                                      controllers_port='8444',
                                      console_use_ssl=True,
                                      console_path='/console',
                                      console_port='8443', etcd_use_ssl=True,
                                      etcd_hosts='', etcd_port='4001',
                                      portal_net='172.30.0.0/16',
                                      embedded_etcd=True, embedded_kube=True,
                                      embedded_dns=True,
                                      bind_addr='0.0.0.0',
                                      session_max_seconds=3600,
                                      session_name='ssn',
                                      session_secrets_file='',
                                      access_token_max_seconds=86400,
                                      auth_token_max_seconds=500,
                                      oauth_grant_method='auto',
                                      dynamic_provisioning_enabled=True,
                                      max_requests_inflight=500)

        if 'node' in roles:
            defaults['node'] = dict(labels={}, annotations={},
                                    iptables_sync_period='30s',
                                    local_quota_per_fsgroup="",
                                    set_node_ip=False)

        if 'docker' in roles:
            docker = dict(disable_push_dockerhub=False,
                          options='--log-driver=journald')
            # NOTE: This is a workaround for a dnf output racecondition that can occur in
            # some situations. See https://bugzilla.redhat.com/show_bug.cgi?id=918184
            if self.system_facts['ansible_pkg_mgr'] == 'dnf':
                rpm_rebuilddb()

            version_info = get_docker_version_info()
            if version_info is not None:
                docker['api_version'] = version_info['api_version']
                docker['version'] = version_info['version']
                docker['gte_1_10'] = LooseVersion(version_info['version']) >= LooseVersion('1.10')
            hosted_registry_insecure = get_hosted_registry_insecure()
            if hosted_registry_insecure is not None:
                docker['hosted_registry_insecure'] = hosted_registry_insecure
            docker['service_name'] = 'docker'
            defaults['docker'] = docker

        if 'clock' in roles:
            exit_code, _, _ = module.run_command(['rpm', '-q', 'chrony'])  # noqa: F405
            chrony_installed = bool(exit_code == 0)
            defaults['clock'] = dict(
                enabled=True,
                chrony_installed=chrony_installed)

        if 'cloudprovider' in roles:
            defaults['cloudprovider'] = dict(kind=None)

        if 'hosted' in roles or self.role == 'hosted':
            defaults['hosted'] = dict(
                metrics=dict(
                    deploy=False,
                    duration=7,
                    resolution='10s',
                    storage=dict(
                        kind=None,
                        volume=dict(
                            name='metrics',
                            size='10Gi'
                        ),
                        nfs=dict(
                            directory='/exports',
                            options='*(rw,root_squash)'
                        ),
                        host=None,
                        access=dict(
                            modes=['ReadWriteOnce']
                        ),
                        create_pv=True,
                        create_pvc=False
                    )
                ),
                loggingops=dict(
                    storage=dict(
                        kind=None,
                        volume=dict(
                            name='logging-es-ops',
                            size='10Gi'
                        ),
                        nfs=dict(
                            directory='/exports',
                            options='*(rw,root_squash)'
                        ),
                        host=None,
                        access=dict(
                            modes=['ReadWriteOnce']
                        ),
                        create_pv=True,
                        create_pvc=False
                    )
                ),
                logging=dict(
                    storage=dict(
                        kind=None,
                        volume=dict(
                            name='logging-es',
                            size='10Gi'
                        ),
                        nfs=dict(
                            directory='/exports',
                            options='*(rw,root_squash)'
                        ),
                        host=None,
                        access=dict(
                            modes=['ReadWriteOnce']
                        ),
                        create_pv=True,
                        create_pvc=False
                    )
                ),
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
                        glusterfs=dict(
                            endpoints='glusterfs-registry-endpoints',
                            path='glusterfs-registry-volume',
                            readOnly=False,
                            swap=False,
                            swapcopy=True),
                        host=None,
                        access=dict(
                            modes=['ReadWriteMany']
                        ),
                        create_pv=True,
                        create_pvc=True
                    )
                ),
                router=dict()
            )

        return defaults

    def guess_host_provider(self):
        """ Guess the host provider

            Returns:
                dict: The generated default facts for the detected provider
        """
        # TODO: cloud provider facts should probably be submitted upstream
        product_name = self.system_facts['ansible_product_name']
        product_version = self.system_facts['ansible_product_version']
        virt_type = self.system_facts['ansible_virtualization_type']
        virt_role = self.system_facts['ansible_virtualization_role']
        provider = None
        metadata = None

        # TODO: this is not exposed through module_utils/facts.py in ansible,
        # need to create PR for ansible to expose it
        bios_vendor = get_file_content(  # noqa: F405
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
        elif virt_type == 'xen' and virt_role == 'guest' and re.match(r'.*\.amazon$', product_version):
            provider = 'aws'
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

    @staticmethod
    def split_openshift_env_fact_keys(openshift_env_fact, openshift_env_structures):
        """ Split openshift_env facts based on openshift_env structures.

            Args:
                openshift_env_fact (string): the openshift_env fact to split
                                             ex: 'openshift_cloudprovider_openstack_auth_url'
                openshift_env_structures (list): a list of structures to determine fact keys
                                                 ex: ['openshift.cloudprovider.openstack.*']
            Returns:
                list: a list of keys that represent the fact
                      ex: ['openshift', 'cloudprovider', 'openstack', 'auth_url']
        """
        # By default, we'll split an openshift_env fact by underscores.
        fact_keys = openshift_env_fact.split('_')

        # Determine if any of the provided variable structures match the fact.
        matching_structure = None
        if openshift_env_structures is not None:
            for structure in openshift_env_structures:
                if re.match(structure, openshift_env_fact):
                    matching_structure = structure
        # Fact didn't match any variable structures so return the default fact keys.
        if matching_structure is None:
            return fact_keys

        final_keys = []
        structure_keys = matching_structure.split('.')
        for structure_key in structure_keys:
            # Matched current key. Add to final keys.
            if structure_key == fact_keys[structure_keys.index(structure_key)]:
                final_keys.append(structure_key)
            # Wildcard means we will be taking everything from here to the end of the fact.
            elif structure_key == '*':
                final_keys.append('_'.join(fact_keys[structure_keys.index(structure_key):]))
            # Shouldn't have gotten here, return the fact keys.
            else:
                return fact_keys
        return final_keys

    # Disabling too-many-branches and too-many-locals.
    # This should be cleaned up as a TODO item.
    # pylint: disable=too-many-branches, too-many-locals
    def init_local_facts(self, facts=None,
                         additive_facts_to_overwrite=None,
                         openshift_env=None,
                         openshift_env_structures=None,
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

        if openshift_env != {} and openshift_env is not None:
            for fact, value in iteritems(openshift_env):
                oo_env_facts = dict()
                current_level = oo_env_facts
                keys = self.split_openshift_env_fact_keys(fact, openshift_env_structures)[1:]
                if len(keys) > 0 and keys[0] != self.role:
                    continue
                for key in keys:
                    if key == keys[-1]:
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
            # remove duplicate and empty strings from registry lists, preserving order
            for cat in ['additional', 'blocked', 'insecure']:
                key = '{0}_registries'.format(cat)
                if key in new_local_facts['docker']:
                    val = new_local_facts['docker'][key]
                    if isinstance(val, string_types):
                        val = [x.strip() for x in val.split(',')]
                    seen = set()
                    new_local_facts['docker'][key] = list()
                    for registry in val:
                        if registry not in seen and registry != '':
                            seen.add(registry)
                            new_local_facts['docker'][key].append(registry)
            # Convert legacy log_options comma sep string to a list if present:
            if 'log_options' in new_local_facts['docker'] and \
                    isinstance(new_local_facts['docker']['log_options'], string_types):
                new_local_facts['docker']['log_options'] = new_local_facts['docker']['log_options'].split(',')

        new_local_facts = self.remove_empty_facts(new_local_facts)

        if new_local_facts != local_facts:
            self.validate_local_facts(new_local_facts)
            changed = True
            if not module.check_mode:  # noqa: F405
                save_local_facts(self.filename, new_local_facts)

        self.changed = changed
        return new_local_facts

    def remove_empty_facts(self, facts=None):
        """ Remove empty facts

            Args:
                facts (dict): facts to clean
        """
        facts_to_remove = []
        for fact, value in iteritems(facts):
            if isinstance(facts[fact], dict):
                facts[fact] = self.remove_empty_facts(facts[fact])
            else:
                if value == "" or value == [""] or value is None:
                    facts_to_remove.append(fact)
        for fact in facts_to_remove:
            del facts[fact]
        return facts

    def validate_local_facts(self, facts=None):
        """ Validate local facts

            Args:
                facts (dict): local facts to validate
        """
        invalid_facts = dict()
        invalid_facts = self.validate_master_facts(facts, invalid_facts)
        if invalid_facts:
            msg = 'Invalid facts detected:\n'
            # pylint: disable=consider-iterating-dictionary
            for key in invalid_facts.keys():
                msg += '{0}: {1}\n'.format(key, invalid_facts[key])
            module.fail_json(msg=msg, changed=self.changed)  # noqa: F405

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
    module = AnsibleModule(  # noqa: F405
        argument_spec=dict(
            role=dict(default='common', required=False,
                      choices=OpenShiftFacts.known_roles),
            local_facts=dict(default=None, type='dict', required=False),
            additive_facts_to_overwrite=dict(default=[], type='list', required=False),
            openshift_env=dict(default={}, type='dict', required=False),
            openshift_env_structures=dict(default=[], type='list', required=False),
            protected_facts_to_overwrite=dict(default=[], type='list', required=False)
        ),
        supports_check_mode=True,
        add_file_common_args=True,
    )

    if not HAVE_DBUS:
        module.fail_json(msg="This module requires dbus python bindings")  # noqa: F405

    module.params['gather_subset'] = ['hardware', 'network', 'virtual', 'facter']  # noqa: F405
    module.params['gather_timeout'] = 10  # noqa: F405
    module.params['filter'] = '*'  # noqa: F405

    role = module.params['role']  # noqa: F405
    local_facts = module.params['local_facts']  # noqa: F405
    additive_facts_to_overwrite = module.params['additive_facts_to_overwrite']  # noqa: F405
    openshift_env = module.params['openshift_env']  # noqa: F405
    openshift_env_structures = module.params['openshift_env_structures']  # noqa: F405
    protected_facts_to_overwrite = module.params['protected_facts_to_overwrite']  # noqa: F405

    fact_file = '/etc/ansible/facts.d/openshift.fact'

    openshift_facts = OpenShiftFacts(role,
                                     fact_file,
                                     local_facts,
                                     additive_facts_to_overwrite,
                                     openshift_env,
                                     openshift_env_structures,
                                     protected_facts_to_overwrite)

    file_params = module.params.copy()  # noqa: F405
    file_params['path'] = fact_file
    file_args = module.load_file_common_arguments(file_params)  # noqa: F405
    changed = module.set_fs_attributes_if_different(file_args,  # noqa: F405
                                                    openshift_facts.changed)

    return module.exit_json(changed=changed,  # noqa: F405
                            ansible_facts=openshift_facts.facts)


if __name__ == '__main__':
    main()
