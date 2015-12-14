# vim: expandtab:tabstop=4:shiftwidth=4

"""This module comprises Aws specific utility functions."""

import os
import re

# Buildbot does not have multi_inventory installed
#pylint: disable=no-name-in-module
from openshift_ansible import multi_inventory

class ArgumentError(Exception):
    """This class is raised when improper arguments are passed."""

    def __init__(self, message):
        """Initialize an ArgumentError.

        Keyword arguments:
        message -- the exact error message being raised
        """
        super(ArgumentError, self).__init__()
        self.message = message

class AwsUtil(object):
    """This class contains the AWS utility functions."""

    def __init__(self, host_type_aliases=None):
        """Initialize the AWS utility class.

        Keyword arguments:
        host_type_aliases -- a list of aliases to common host-types (e.g. ex-node)
        """

        host_type_aliases = host_type_aliases or {}

        self.host_type_aliases = host_type_aliases
        self.file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)))

        self.setup_host_type_alias_lookup()

    def setup_host_type_alias_lookup(self):
        """Sets up the alias to host-type lookup table."""
        self.alias_lookup = {}
        for key, values in self.host_type_aliases.iteritems():
            for value in values:
                self.alias_lookup[value] = key

    @staticmethod
    def get_inventory(args=None, cached=False):
        """Calls the inventory script and returns a dictionary containing the inventory."

        Keyword arguments:
        args -- optional arguments to pass to the inventory script
        """
        minv = multi_inventory.MultiInventory(args)
        if cached:
            minv.get_inventory_from_cache()
        else:
            minv.run()
        return minv.result

    def get_environments(self):
        """Searches for env tags in the inventory and returns all of the envs found."""
        pattern = re.compile(r'^tag_env_(.*)')

        envs = []
        inv = self.get_inventory()
        for key in inv.keys():
            matched = pattern.match(key)
            if matched:
                envs.append(matched.group(1))

        envs.sort()
        return envs

    def get_host_types(self):
        """Searches for host-type tags in the inventory and returns all host-types found."""
        pattern = re.compile(r'^tag_host-type_(.*)')

        host_types = []
        inv = self.get_inventory()
        for key in inv.keys():
            matched = pattern.match(key)
            if matched:
                host_types.append(matched.group(1))

        host_types.sort()
        return host_types

    def get_security_groups(self):
        """Searches for security_groups in the inventory and returns all SGs found."""
        pattern = re.compile(r'^security_group_(.*)')

        groups = []
        inv = self.get_inventory()
        for key in inv.keys():
            matched = pattern.match(key)
            if matched:
                groups.append(matched.group(1))

        groups.sort()
        return groups

    def build_host_dict_by_env(self, args=None):
        """Searches the inventory for hosts in an env and returns their hostvars."""
        args = args or []
        inv = self.get_inventory(args)

        inst_by_env = {}
        for _, host in inv['_meta']['hostvars'].items():
            # If you don't have an environment tag, we're going to ignore you
            if 'ec2_tag_env' not in host:
                continue

            if host['ec2_tag_env'] not in inst_by_env:
                inst_by_env[host['ec2_tag_env']] = {}
            host_id = "%s:%s" % (host['ec2_tag_Name'], host['ec2_id'])
            inst_by_env[host['ec2_tag_env']][host_id] = host

        return inst_by_env

    def print_host_types(self):
        """Gets the list of host types and aliases and outputs them in columns."""
        host_types = self.get_host_types()
        ht_format_str = "%35s"
        alias_format_str = "%-20s"
        combined_format_str = ht_format_str + "    " + alias_format_str

        print
        print combined_format_str % ('Host Types', 'Aliases')
        print combined_format_str % ('----------', '-------')

        for host_type in host_types:
            aliases = []
            if host_type in self.host_type_aliases:
                aliases = self.host_type_aliases[host_type]
                print combined_format_str % (host_type, ", ".join(aliases))
            else:
                print  ht_format_str % host_type
        print

    def resolve_host_type(self, host_type):
        """Converts a host-type alias into a host-type.

        Keyword arguments:
        host_type -- The alias or host_type to look up.

        Example (depends on aliases defined in config file):
            host_type = ex-node
            returns: openshift-node
        """
        if self.alias_lookup.has_key(host_type):
            return self.alias_lookup[host_type]
        return host_type

    @staticmethod
    def gen_env_tag(env):
        """Generate the environment tag
        """
        return "tag_env_%s" % env

    def gen_host_type_tag(self, host_type):
        """Generate the host type tag
        """
        host_type = self.resolve_host_type(host_type)
        return "tag_host-type_%s" % host_type

    def gen_env_host_type_tag(self, host_type, env):
        """Generate the environment host type tag
        """
        host_type = self.resolve_host_type(host_type)
        return "tag_env-host-type_%s-%s" % (env, host_type)

    def get_host_list(self, host_type=None, envs=None, version=None, cached=False):
        """Get the list of hosts from the inventory using host-type and environment
        """
        retval = set([])
        envs = envs or []
        inv = self.get_inventory(cached=cached)

        # We prefer to deal with a list of environments
        if issubclass(type(envs), basestring):
            if envs == 'all':
                envs = self.get_environments()
            else:
                envs = [envs]

        if host_type and envs:
            # Both host type and environment were specified
            for env in envs:
                retval.update(inv.get('tag_environment_%s' % env, []))
            retval.intersection_update(inv.get(self.gen_host_type_tag(host_type), []))

        elif envs and not host_type:
            # Just environment was specified
            for env in envs:
                env_tag = AwsUtil.gen_env_tag(env)
                if env_tag in inv.keys():
                    retval.update(inv.get(env_tag, []))

        elif host_type and not envs:
            # Just host-type was specified
            host_type_tag = self.gen_host_type_tag(host_type)
            if host_type_tag in inv.keys():
                retval.update(inv.get(host_type_tag, []))

        # If version is specified then return only hosts in that version
        if version:
            retval.intersection_update(inv.get('oo_version_%s' % version, []))

        return retval
