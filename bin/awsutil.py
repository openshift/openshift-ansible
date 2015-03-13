# vim: expandtab:tabstop=4:shiftwidth=4

import subprocess
import os
import json
import re

class AwsUtil(object):
    def __init__(self):
        self.host_type_aliases = {
                'legacy-openshift-broker': ['broker', 'ex-srv'],
                         'openshift-node': ['node', 'ex-node'],
                   'openshift-messagebus': ['msg'],
            'openshift-customer-database': ['mongo'],
                'openshift-website-proxy': ['proxy'],
            'openshift-community-website': ['drupal'],
                         'package-mirror': ['mirror'],
        }

        self.alias_lookup = {}
        for key, values in self.host_type_aliases.iteritems():
            for value in values:
                self.alias_lookup[value] = key

        self.file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)))
        self.multi_ec2_path = os.path.realpath(os.path.join(self.file_path, '..','inventory','multi_ec2.py'))

    def get_inventory(self,args=[]):
        cmd = [self.multi_ec2_path]

        if args:
            cmd.extend(args)

        env = os.environ

        p = subprocess.Popen(cmd, stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE, env=env)

        out,err = p.communicate()

        if p.returncode != 0:
            raise RuntimeError(err)

        return json.loads(out.strip())

    def get_environments(self):
        pattern = re.compile(r'^tag_environment_(.*)')

        envs = []
        inv = self.get_inventory()
        for key in inv.keys():
            m = pattern.match(key)
            if m:
                envs.append(m.group(1))

        envs.sort()
        return envs

    def get_host_types(self):
        pattern = re.compile(r'^tag_host-type_(.*)')

        host_types = []
        inv = self.get_inventory()
        for key in inv.keys():
            m = pattern.match(key)
            if m:
                host_types.append(m.group(1))

        host_types.sort()
        return host_types

    def get_security_groups(self):
        pattern = re.compile(r'^security_group_(.*)')

        groups = []
        inv = self.get_inventory()
        for key in inv.keys():
            m = pattern.match(key)
            if m:
                groups.append(m.group(1))

        groups.sort()
        return groups

    def build_host_dict_by_env(self, args=[]):
        inv = self.get_inventory(args)

        inst_by_env = {}
        for dns, host in inv['_meta']['hostvars'].items():
            # If you don't have an environment tag, we're going to ignore you
            if 'ec2_tag_environment' not in host:
                continue

            if host['ec2_tag_environment'] not in inst_by_env:
                inst_by_env[host['ec2_tag_environment']] = {}
            host_id = "%s:%s" % (host['ec2_tag_Name'],host['ec2_id'])
            inst_by_env[host['ec2_tag_environment']][host_id] = host

        return inst_by_env

    # Display host_types
    def print_host_types(self):
        host_types = self.get_host_types()
        ht_format_str = "%35s"
        alias_format_str = "%-20s"
        combined_format_str = ht_format_str + "    " + alias_format_str

        print
        print combined_format_str % ('Host Types', 'Aliases')
        print combined_format_str % ('----------', '-------')

        for ht in host_types:
            aliases = []
            if ht in self.host_type_aliases:
                aliases = self.host_type_aliases[ht]
                print combined_format_str % (ht, ", ".join(aliases))
            else:
                print  ht_format_str % ht
        print

    # Convert host-type aliases to real a host-type
    def resolve_host_type(self, host_type):
        if self.alias_lookup.has_key(host_type):
            return self.alias_lookup[host_type]
        return host_type

    def gen_env_host_type_tag(self, host_type, env):
        """Generate the environment host type tag
        """
        host_type = self.resolve_host_type(host_type)
        return "tag_env-host-type_%s-%s" % (env, host_type)

    def get_host_list(self, host_type, env):
        """Get the list of hosts from the inventory using host-type and environment
        """
        inv = self.get_inventory()
        host_type_tag = self.gen_env_host_type_tag(host_type, env)
        return inv[host_type_tag]
