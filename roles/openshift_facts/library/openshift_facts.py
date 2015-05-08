#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4
# disable pylint checks
# temporarily disabled until items can be addressed:
#   fixme - until all TODO comments have been addressed
# pylint:disable=fixme
"""Ansible module for retrieving and setting openshift related facts"""

DOCUMENTATION = '''
---
module: openshift_facts
short_description: OpenShift Facts
author: Jason DeTiberus
requirements: [ ]
'''
EXAMPLES = '''
'''

import ConfigParser
import copy


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
    facts['external_id'] = metadata['instance']['id']

    # Default to no sdn for GCE deployments
    facts['use_openshift_sdn'] = False

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
            ips = interface[int_var]
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
    facts['external_id'] = metadata['instance-id']

    # TODO: actually attempt to determine default local and public ips
    # by using the ansible default ip fact and the ipv4-associations
    # from the ec2 metadata
    facts['network']['ip'] = metadata['local-ipv4']
    facts['network']['public_ip'] = metadata['public-ipv4']

    # TODO: verify that local hostname makes sense and is resolvable
    facts['network']['hostname'] = metadata['local-hostname']

    # TODO: verify that public hostname makes sense and is resolvable
    facts['network']['public_hostname'] = metadata['public-hostname']

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
    facts['external_id'] = metadata['uuid']
    facts['network']['ip'] = metadata['ec2_compat']['local-ipv4']
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
    if provider == 'gce':
        facts = normalize_gce_facts(metadata, facts)
    elif provider == 'ec2':
        facts = normalize_aws_facts(metadata, facts)
    elif provider == 'openstack':
        facts = normalize_openstack_facts(metadata, facts)
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
        for (url_var, use_ssl, port, default) in [
                ('api_url',
                 facts['master']['api_use_ssl'],
                 facts['master']['api_port'],
                 facts['common']['hostname']),
                ('public_api_url',
                 facts['master']['api_use_ssl'],
                 facts['master']['api_port'],
                 facts['common']['public_hostname']),
                ('console_url',
                 facts['master']['console_use_ssl'],
                 facts['master']['console_port'],
                 facts['common']['hostname']),
                ('public_console_url' 'console_use_ssl',
                 facts['master']['console_use_ssl'],
                 facts['master']['console_port'],
                 facts['common']['public_hostname'])]:
            if url_var not in facts['master']:
                scheme = 'https' if use_ssl else 'http'
                netloc = default
                if ((scheme == 'https' and port != '443')
                        or (scheme == 'http' and port != '80')):
                    netloc = "%s:%s" % (netloc, port)
                facts['master'][url_var] = urlparse.urlunparse(
                    (scheme, netloc, '', '', '', '')
                )
    return facts


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

        # Query kubeconfig settings
        kubeconfig_dir = '/var/lib/openshift/openshift.local.certificates'
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
            # to bubble up any exceptions if openshift ex config view
            # fails
            # pylint: disable=broad-except
            except Exception:
                pass

    return current_config


def apply_provider_facts(facts, provider_facts, roles):
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

    use_openshift_sdn = provider_facts.get('use_openshift_sdn')
    if isinstance(use_openshift_sdn, bool):
        facts['common']['use_openshift_sdn'] = use_openshift_sdn

    common_vars = [('hostname', 'ip'), ('public_hostname', 'public_ip')]
    for h_var, ip_var in common_vars:
        ip_value = provider_facts['network'].get(ip_var)
        if ip_value:
            facts['common'][ip_var] = ip_value

        facts['common'][h_var] = choose_hostname(
            [provider_facts['network'].get(h_var)],
            facts['common'][ip_var]
        )

    if 'node' in roles:
        ext_id = provider_facts.get('external_id')
        if ext_id:
            facts['node']['external_id'] = ext_id

    facts['provider'] = provider_facts
    return facts


def merge_facts(orig, new):
    """ Recursively merge facts dicts

        Args:
            orig (dict): existing facts
            new (dict): facts to update
        Returns:
            dict: the merged facts
    """
    facts = dict()
    for key, value in orig.iteritems():
        if key in new:
            if isinstance(value, dict):
                facts[key] = merge_facts(value, new[key])
            else:
                facts[key] = copy.copy(new[key])
        else:
            facts[key] = copy.deepcopy(value)
    new_keys = set(new.keys()) - set(orig.keys())
    for key in new_keys:
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
        if not os.path.exists(fact_dir):
            os.makedirs(fact_dir)
        with open(filename, 'w') as fact_file:
            fact_file.write(module.jsonify(facts))
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


class OpenShiftFactsUnsupportedRoleError(Exception):
    """OpenShift Facts Unsupported Role Error"""
    pass


class OpenShiftFactsFileWriteError(Exception):
    """OpenShift Facts File Write Error"""
    pass


class OpenShiftFactsMetadataUnavailableError(Exception):
    """OpenShift Facts Metadata Unavailable Error"""
    pass


class OpenShiftFacts(object):
    """ OpenShift Facts

        Attributes:
            facts (dict): OpenShift facts for the host

        Args:
            role (str): role for setting local facts
            filename (str): local facts file to use
            local_facts (dict): local facts to set

        Raises:
            OpenShiftFactsUnsupportedRoleError:
    """
    known_roles = ['common', 'master', 'node', 'master_sdn', 'node_sdn', 'dns']

    def __init__(self, role, filename, local_facts):
        self.changed = False
        self.filename = filename
        if role not in self.known_roles:
            raise OpenShiftFactsUnsupportedRoleError(
                "Role %s is not supported by this module" % role
            )
        self.role = role
        self.system_facts = ansible_facts(module)
        self.facts = self.generate_facts(local_facts)

    def generate_facts(self, local_facts):
        """ Generate facts

            Args:
                local_facts (dict): local_facts for overriding generated
                                    defaults

            Returns:
                dict: The generated facts
        """
        local_facts = self.init_local_facts(local_facts)
        roles = local_facts.keys()

        defaults = self.get_defaults(roles)
        provider_facts = self.init_provider_facts()
        facts = apply_provider_facts(defaults, provider_facts, roles)
        facts = merge_facts(facts, local_facts)
        facts['current_config'] = get_current_config(facts)
        facts = set_url_facts_if_unset(facts)
        return dict(openshift=facts)

    def get_defaults(self, roles):
        """ Get default fact values

            Args:
                roles (list): list of roles for this host

            Returns:
                dict: The generated default facts
        """
        defaults = dict()

        common = dict(use_openshift_sdn=True)
        ip_addr = self.system_facts['default_ipv4']['address']
        common['ip'] = ip_addr
        common['public_ip'] = ip_addr

        exit_code, output, _ = module.run_command(['hostname', '-f'])
        hostname_f = output.strip() if exit_code == 0 else ''
        hostname_values = [hostname_f, self.system_facts['nodename'],
                           self.system_facts['fqdn']]
        hostname = choose_hostname(hostname_values)

        common['hostname'] = hostname
        common['public_hostname'] = hostname
        defaults['common'] = common

        if 'master' in roles:
            master = dict(api_use_ssl=True, api_port='8443',
                          console_use_ssl=True, console_path='/console',
                          console_port='8443', etcd_use_ssl=False,
                          etcd_port='4001', portal_net='172.30.17.0/24')
            defaults['master'] = master

        if 'node' in roles:
            node = dict(external_id=common['hostname'], pod_cidr='',
                        labels={}, annotations={})
            node['resources_cpu'] = self.system_facts['processor_cores']
            node['resources_memory'] = int(
                int(self.system_facts['memtotal_mb']) * 1024 * 1024 * 0.75
            )
            defaults['node'] = node

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

    def init_local_facts(self, facts=None):
        """ Initialize the provider facts

            Args:
                facts (dict): local facts to set

            Returns:
                dict: The result of merging the provided facts with existing
                      local facts
        """
        changed = False
        facts_to_set = {self.role: dict()}
        if facts is not None:
            facts_to_set[self.role] = facts

        local_facts = get_local_facts_from_file(self.filename)

        for arg in ['labels', 'annotations']:
            if arg in facts_to_set and isinstance(facts_to_set[arg],
                                                  basestring):
                facts_to_set[arg] = module.from_json(facts_to_set[arg])

        new_local_facts = merge_facts(local_facts, facts_to_set)
        for facts in new_local_facts.values():
            keys_to_delete = []
            for fact, value in facts.iteritems():
                if value == "" or value is None:
                    keys_to_delete.append(fact)
            for key in keys_to_delete:
                del facts[key]

        if new_local_facts != local_facts:
            changed = True

            if not module.check_mode:
                save_local_facts(self.filename, new_local_facts)

        self.changed = changed
        return new_local_facts


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
        ),
        supports_check_mode=True,
        add_file_common_args=True,
    )

    role = module.params['role']
    local_facts = module.params['local_facts']
    fact_file = '/etc/ansible/facts.d/openshift.fact'

    openshift_facts = OpenShiftFacts(role, fact_file, local_facts)

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
