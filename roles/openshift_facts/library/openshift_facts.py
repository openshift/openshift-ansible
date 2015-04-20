#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4

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

class OpenShiftFactsUnsupportedRoleError(Exception):
    pass

class OpenShiftFactsFileWriteError(Exception):
    pass

class OpenShiftFactsMetadataUnavailableError(Exception):
    pass

class OpenShiftFacts():
    known_roles = ['common', 'master', 'node', 'master_sdn', 'node_sdn', 'dns']

    def __init__(self, role, filename, local_facts):
        self.changed = False
        self.filename = filename
        if role not in self.known_roles:
            raise OpenShiftFactsUnsupportedRoleError("Role %s is not supported by this module" % role)
        self.role = role
        self.facts = self.generate_facts(local_facts)

    def generate_facts(self, local_facts):
        local_facts = self.init_local_facts(local_facts)
        roles = local_facts.keys()

        defaults = self.get_defaults(roles)
        provider_facts = self.init_provider_facts()
        facts = self.apply_provider_facts(defaults, provider_facts, roles)

        facts = self.merge_facts(facts, local_facts)
        facts['current_config'] = self.current_config(facts)
        self.set_url_facts_if_unset(facts)
        return dict(openshift=facts)


    def set_url_facts_if_unset(self, facts):
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
                    if (scheme == 'https' and port != '443') or (scheme == 'http' and port != '80'):
                        netloc = "%s:%s" % (netloc, port)
                    facts['master'][url_var] = urlparse.urlunparse((scheme, netloc, '', '', '', ''))


    # Query current OpenShift config and return a dictionary containing
    # settings that may be valuable for determining actions that need to be
    # taken in the playbooks/roles
    def current_config(self, facts):
        current_config=dict()
        roles = [ role for role in facts if role not in ['common','provider'] ]
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
                kubeconfig_dir = os.path.join(kubeconfig_dir, "node-%s" % facts['common']['hostname'])

            kubeconfig_path = os.path.join(kubeconfig_dir, '.kubeconfig')
            if os.path.isfile('/usr/bin/openshift') and os.path.isfile(kubeconfig_path):
                try:
                    _, output, error = module.run_command(["/usr/bin/openshift", "ex",
                                                           "config", "view", "-o",
                                                           "json",
                                                           "--kubeconfig=%s" % kubeconfig_path],
                                                           check_rc=False)
                    config = json.loads(output)

                    try:
                        for cluster in config['clusters']:
                            config['clusters'][cluster]['certificate-authority-data'] = 'masked'
                    except KeyError:
                        pass
                    try:
                        for user in config['users']:
                            config['users'][user]['client-certificate-data'] = 'masked'
                            config['users'][user]['client-key-data'] = 'masked'
                    except KeyError:
                        pass

                    current_config['kubeconfig'] = config
                except Exception:
                    pass

        return current_config


    def apply_provider_facts(self, facts, provider_facts, roles):
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

            facts['common'][h_var] = self.choose_hostname([provider_facts['network'].get(h_var)], facts['common'][ip_var])

        if 'node' in roles:
            ext_id = provider_facts.get('external_id')
            if ext_id:
                facts['node']['external_id'] = ext_id

        facts['provider'] = provider_facts
        return facts

    def hostname_valid(self, hostname):
        if (not hostname or
                hostname.startswith('localhost') or
                hostname.endswith('localdomain') or
                len(hostname.split('.')) < 2):
            return False

        return True

    def choose_hostname(self, hostnames=[], fallback=''):
        hostname = fallback

        ips = [ i for i in hostnames if i is not None and re.match(r'\A\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\Z', i) ]
        hosts = [ i for i in hostnames if i is not None and i not in set(ips) ]

        for host_list in (hosts, ips):
            for h in host_list:
                if self.hostname_valid(h):
                    return h

        return hostname

    def get_defaults(self, roles):
        ansible_facts = self.get_ansible_facts()

        defaults = dict()

        common = dict(use_openshift_sdn=True)
        ip = ansible_facts['default_ipv4']['address']
        common['ip'] = ip
        common['public_ip'] = ip

        rc, output, error = module.run_command(['hostname', '-f'])
        hostname_f = output.strip() if rc == 0 else ''
        hostname_values = [hostname_f, ansible_facts['nodename'], ansible_facts['fqdn']]
        hostname = self.choose_hostname(hostname_values)

        common['hostname'] = hostname
        common['public_hostname'] = hostname
        defaults['common'] = common

        if 'master' in roles:
            # TODO: provide for a better way to override just the port, or just
            # the urls, instead of forcing both, also to override the hostname
            # without having to re-generate these urls later
            master = dict(api_use_ssl=True, api_port='8443',
                    console_use_ssl=True, console_path='/console',
                    console_port='8443', etcd_use_ssl=False,
                    etcd_port='4001', portal_net='172.30.17.0/24')
            defaults['master'] = master

        if 'node' in roles:
            node = dict(external_id=common['hostname'], pod_cidr='',
                        labels={}, annotations={})
            node['resources_cpu'] = ansible_facts['processor_cores']
            node['resources_memory'] = int(int(ansible_facts['memtotal_mb']) * 1024 * 1024 * 0.75)
            defaults['node'] = node

        return defaults

    def merge_facts(self, orig, new):
        facts = dict()
        for key, value in orig.iteritems():
            if key in new:
                if isinstance(value, dict):
                    facts[key] = self.merge_facts(value, new[key])
                else:
                    facts[key] = copy.copy(new[key])
            else:
                facts[key] = copy.deepcopy(value)
        new_keys = set(new.keys()) - set(orig.keys())
        for key in new_keys:
            facts[key] = copy.deepcopy(new[key])
        return facts

    def query_metadata(self, metadata_url, headers=None, expect_json=False):
        r, info = fetch_url(module, metadata_url, headers=headers)
        if info['status'] != 200:
            raise OpenShiftFactsMetadataUnavailableError("Metadata unavailable")
        if expect_json:
            return module.from_json(r.read())
        else:
            return [line.strip() for line in r.readlines()]

    def walk_metadata(self, metadata_url, headers=None, expect_json=False):
        metadata = dict()

        for line in self.query_metadata(metadata_url, headers, expect_json):
            if line.endswith('/') and not line == 'public-keys/':
                key = line[:-1]
                metadata[key]=self.walk_metadata(metadata_url + line, headers,
                                                 expect_json)
            else:
                results = self.query_metadata(metadata_url + line, headers,
                                              expect_json)
                if len(results) == 1:
                    metadata[line] = results.pop()
                else:
                    metadata[line] = results
        return metadata

    def get_provider_metadata(self, metadata_url, supports_recursive=False,
                          headers=None, expect_json=False):
        try:
            if supports_recursive:
                metadata = self.query_metadata(metadata_url, headers, expect_json)
            else:
                metadata = self.walk_metadata(metadata_url, headers, expect_json)
        except OpenShiftFactsMetadataUnavailableError as e:
            metadata = None
        return metadata

    def get_ansible_facts(self):
        if not hasattr(self, 'ansible_facts'):
            self.ansible_facts = ansible_facts(module)
        return self.ansible_facts

    def guess_host_provider(self):
        # TODO: cloud provider facts should probably be submitted upstream
        ansible_facts = self.get_ansible_facts()
        product_name = ansible_facts['product_name']
        product_version = ansible_facts['product_version']
        virt_type = ansible_facts['virtualization_type']
        virt_role = ansible_facts['virtualization_role']
        provider = None
        metadata = None

        # TODO: this is not exposed through module_utils/facts.py in ansible,
        # need to create PR for ansible to expose it
        bios_vendor = get_file_content('/sys/devices/virtual/dmi/id/bios_vendor')
        if bios_vendor == 'Google':
            provider = 'gce'
            metadata_url = 'http://metadata.google.internal/computeMetadata/v1/?recursive=true'
            headers = {'Metadata-Flavor': 'Google'}
            metadata = self.get_provider_metadata(metadata_url, True, headers,
                                                  True)

            # Filter sshKeys and serviceAccounts from gce metadata
            if metadata:
                metadata['project']['attributes'].pop('sshKeys', None)
                metadata['instance'].pop('serviceAccounts', None)
        elif virt_type == 'xen' and virt_role == 'guest' and re.match(r'.*\.amazon$', product_version):
            provider = 'ec2'
            metadata_url = 'http://169.254.169.254/latest/meta-data/'
            metadata = self.get_provider_metadata(metadata_url)
        elif re.search(r'OpenStack', product_name):
            provider = 'openstack'
            metadata_url = 'http://169.254.169.254/openstack/latest/meta_data.json'
            metadata = self.get_provider_metadata(metadata_url, True, None, True)

            if metadata:
                ec2_compat_url = 'http://169.254.169.254/latest/meta-data/'
                metadata['ec2_compat'] = self.get_provider_metadata(ec2_compat_url)

                # Filter public_keys  and random_seed from openstack metadata
                metadata.pop('public_keys', None)
                metadata.pop('random_seed', None)

                if not metadata['ec2_compat']:
                    metadata = None

        return dict(name=provider, metadata=metadata)

    def normalize_provider_facts(self, provider, metadata):
        if provider is None or metadata is None:
            return {}

        # TODO: test for ipv6_enabled where possible (gce, aws do not support)
        # and configure ipv6 facts if available

        # TODO: add support for setting user_data if available

        facts = dict(name=provider, metadata=metadata)
        network = dict(interfaces=[], ipv6_enabled=False)
        if provider == 'gce':
            for interface in metadata['instance']['networkInterfaces']:
                int_info = dict(ips=[interface['ip']], network_type=provider)
                int_info['public_ips'] = [ ac['externalIp'] for ac in interface['accessConfigs'] ]
                int_info['public_ips'].extend(interface['forwardedIps'])
                _, _, network_id = interface['network'].rpartition('/')
                int_info['network_id'] = network_id
                network['interfaces'].append(int_info)
            _, _, zone = metadata['instance']['zone'].rpartition('/')
            facts['zone'] = zone
            facts['external_id'] = metadata['instance']['id']

            # Default to no sdn for GCE deployments
            facts['use_openshift_sdn'] = False

            # GCE currently only supports a single interface
            network['ip'] = network['interfaces'][0]['ips'][0]
            network['public_ip'] = network['interfaces'][0]['public_ips'][0]
            network['hostname'] = metadata['instance']['hostname']

            # TODO: attempt to resolve public_hostname
            network['public_hostname'] = network['public_ip']
        elif provider == 'ec2':
            for interface in sorted(metadata['network']['interfaces']['macs'].values(),
                                    key=lambda x: x['device-number']):
                int_info = dict()
                var_map = {'ips': 'local-ipv4s', 'public_ips': 'public-ipv4s'}
                for ips_var, int_var in var_map.iteritems():
                    ips = interface[int_var]
                    int_info[ips_var] = [ips] if isinstance(ips, basestring) else ips
                int_info['network_type'] = 'vpc' if 'vpc-id' in interface else 'classic'
                int_info['network_id'] = interface['subnet-id'] if int_info['network_type'] == 'vpc' else None
                network['interfaces'].append(int_info)
            facts['zone'] = metadata['placement']['availability-zone']
            facts['external_id'] = metadata['instance-id']

            # TODO: actually attempt to determine default local and public ips
            # by using the ansible default ip fact and the ipv4-associations
            # form the ec2 metadata
            network['ip'] = metadata['local-ipv4']
            network['public_ip'] = metadata['public-ipv4']

            # TODO: verify that local hostname makes sense and is resolvable
            network['hostname'] = metadata['local-hostname']

            # TODO: verify that public hostname makes sense and is resolvable
            network['public_hostname'] = metadata['public-hostname']
        elif provider == 'openstack':
            # openstack ec2 compat api does not support network interfaces and
            # the version tested on did not include the info in the openstack
            # metadata api, should be updated if neutron exposes this.

            facts['zone'] = metadata['availability_zone']
            facts['external_id'] = metadata['uuid']
            network['ip'] = metadata['ec2_compat']['local-ipv4']
            network['public_ip'] = metadata['ec2_compat']['public-ipv4']

            # TODO: verify local hostname makes sense and is resolvable
            network['hostname'] = metadata['hostname']

            # TODO: verify that public hostname makes sense and is resolvable
            network['public_hostname'] = metadata['ec2_compat']['public-hostname']

        facts['network'] = network
        return facts

    def init_provider_facts(self):
        provider_info = self.guess_host_provider()
        provider_facts = self.normalize_provider_facts(
                provider_info.get('name'),
                provider_info.get('metadata')
        )
        return provider_facts

    def get_facts(self):
        # TODO: transform facts into cleaner format (openshift_<blah> instead
        # of openshift.<blah>
        return self.facts

    def init_local_facts(self, facts={}):
        changed = False

        local_facts = ConfigParser.SafeConfigParser()
        local_facts.read(self.filename)

        section = self.role
        if not local_facts.has_section(section):
            local_facts.add_section(section)
            changed = True

        for key, value in facts.iteritems():
            if isinstance(value, bool):
                value = str(value)
            if not value:
                continue
            if not local_facts.has_option(section, key) or local_facts.get(section, key) != value:
                local_facts.set(section, key, value)
                changed = True

        if changed and not module.check_mode:
            try:
                fact_dir = os.path.dirname(self.filename)
                if not os.path.exists(fact_dir):
                    os.makedirs(fact_dir)
                with open(self.filename, 'w') as fact_file:
                        local_facts.write(fact_file)
            except (IOError, OSError) as e:
                raise OpenShiftFactsFileWriteError("Could not create fact file: %s, error: %s" % (self.filename, e))
        self.changed = changed

        role_facts = dict()
        for section in local_facts.sections():
            role_facts[section] = dict()
            for opt, val in local_facts.items(section):
                role_facts[section][opt] = val
        return role_facts


def main():
    global module
    module = AnsibleModule(
            argument_spec = dict(
                    role=dict(default='common',
                              choices=OpenShiftFacts.known_roles,
                              required=False),
                    local_facts=dict(default={}, type='dict', required=False),
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
            ansible_facts=openshift_facts.get_facts())

# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.facts import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
