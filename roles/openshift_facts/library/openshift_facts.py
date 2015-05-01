#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4
# disable pylint checks
# temporarily disabled until items can be addressed:
#   fixme - until all TODO comments have been addressed
# permanently disabled unless someone wants to refactor the object model:
    #   no-self-use
    #   too-many-locals
    #   too-many-branches
    # pylint:disable=fixme, no-self-use
    # pylint:disable=too-many-locals, too-many-branches

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

class OpenShiftFacts(object):
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
                    if ((scheme == 'https' and port != '443')
                            or (scheme == 'http' and port != '80')):
                        netloc = "%s:%s" % (netloc, port)
                    facts['master'][url_var] = urlparse.urlunparse(
                        (scheme, netloc, '', '', '', '')
                    )


    # Query current OpenShift config and return a dictionary containing
    # settings that may be valuable for determining actions that need to be
    # taken in the playbooks/roles
    def current_config(self, facts):
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

            facts['common'][h_var] = self.choose_hostname(
                [provider_facts['network'].get(h_var)],
                facts['common'][ip_var]
            )

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

    def choose_hostname(self, hostnames=None, fallback=''):
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
                if self.hostname_valid(host):
                    return host

        return hostname

    def get_defaults(self, roles):
        defaults = dict()

        common = dict(use_openshift_sdn=True)
        ip_addr = self.system_facts['default_ipv4']['address']
        common['ip'] = ip_addr
        common['public_ip'] = ip_addr

        exit_code, output, _ = module.run_command(['hostname', '-f'])
        hostname_f = output.strip() if exit_code == 0 else ''
        hostname_values = [hostname_f, self.system_facts['nodename'],
                           self.system_facts['fqdn']]
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
            node['resources_cpu'] = self.system_facts['processor_cores']
            node['resources_memory'] = int(
                int(self.system_facts['memtotal_mb']) * 1024 * 1024 * 0.75
            )
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
        result, info = fetch_url(module, metadata_url, headers=headers)
        if info['status'] != 200:
            raise OpenShiftFactsMetadataUnavailableError("Metadata unavailable")
        if expect_json:
            return module.from_json(result.read())
        else:
            return [line.strip() for line in result.readlines()]

    def walk_metadata(self, metadata_url, headers=None, expect_json=False):
        metadata = dict()

        for line in self.query_metadata(metadata_url, headers, expect_json):
            if line.endswith('/') and not line == 'public-keys/':
                key = line[:-1]
                metadata[key] = self.walk_metadata(metadata_url + line,
                                                   headers, expect_json)
            else:
                results = self.query_metadata(metadata_url + line, headers,
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

    def get_provider_metadata(self, metadata_url, supports_recursive=False,
                              headers=None, expect_json=False):
        try:
            if supports_recursive:
                metadata = self.query_metadata(metadata_url, headers,
                                               expect_json)
            else:
                metadata = self.walk_metadata(metadata_url, headers,
                                              expect_json)
        except OpenShiftFactsMetadataUnavailableError:
            metadata = None
        return metadata

    # TODO: refactor to reduce the size of this method, potentially create
    # sub-methods (or classes for the different providers)
    # temporarily disable pylint too-many-statements
    # pylint: disable=too-many-statements
    def guess_host_provider(self):
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
            metadata = self.get_provider_metadata(metadata_url, True, headers,
                                                  True)

            # Filter sshKeys and serviceAccounts from gce metadata
            if metadata:
                metadata['project']['attributes'].pop('sshKeys', None)
                metadata['instance'].pop('serviceAccounts', None)
        elif (virt_type == 'xen' and virt_role == 'guest'
              and re.match(r'.*\.amazon$', product_version)):
            provider = 'ec2'
            metadata_url = 'http://169.254.169.254/latest/meta-data/'
            metadata = self.get_provider_metadata(metadata_url)
        elif re.search(r'OpenStack', product_name):
            provider = 'openstack'
            metadata_url = ('http://169.254.169.254/openstack/latest/'
                            'meta_data.json')
            metadata = self.get_provider_metadata(metadata_url, True, None,
                                                  True)

            if metadata:
                ec2_compat_url = 'http://169.254.169.254/latest/meta-data/'
                metadata['ec2_compat'] = self.get_provider_metadata(
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
                int_info['public_ips'] = [ac['externalIp'] for ac
                                          in interface['accessConfigs']]
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
            pub_h = metadata['ec2_compat']['public-hostname']
            network['public_hostname'] = pub_h

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

    def init_local_facts(self, facts=None):
        changed = False
        facts_to_set = {self.role: dict()}
        if facts is not None:
            facts_to_set[self.role] = facts

        # Handle conversion of INI style facts file to json style
        local_facts = dict()
        try:
            ini_facts = ConfigParser.SafeConfigParser()
            ini_facts.read(self.filename)
            for section in ini_facts.sections():
                local_facts[section] = dict()
                for key, value in ini_facts.items(section):
                    local_facts[section][key] = value

        except (ConfigParser.MissingSectionHeaderError,
                ConfigParser.ParsingError):
            try:
                with open(self.filename, 'r') as facts_file:
                    local_facts = json.load(facts_file)

            except (ValueError, IOError) as ex:
                pass

        for arg in ['labels', 'annotations']:
            if arg in facts_to_set and isinstance(facts_to_set[arg],
                                                  basestring):
                facts_to_set[arg] = module.from_json(facts_to_set[arg])

        new_local_facts = self.merge_facts(local_facts, facts_to_set)
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
                try:
                    fact_dir = os.path.dirname(self.filename)
                    if not os.path.exists(fact_dir):
                        os.makedirs(fact_dir)
                    with open(self.filename, 'w') as fact_file:
                        fact_file.write(module.jsonify(new_local_facts))
                except (IOError, OSError) as ex:
                    raise OpenShiftFactsFileWriteError(
                        "Could not create fact file: "
                        "%s, error: %s" % (self.filename, ex)
                    )
        self.changed = changed
        return new_local_facts


def main():
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
                            ansible_facts=openshift_facts.get_facts())

# ignore pylint errors related to the module_utils import
# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import
# import module snippets
from ansible.module_utils.basic import *
from ansible.module_utils.facts import *
from ansible.module_utils.urls import *

if __name__ == '__main__':
    main()
