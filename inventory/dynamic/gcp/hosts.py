#!/usr/bin/env python
# Copyright 2013 Google Inc.
#
# This file is part of Ansible
#
# Ansible is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

# This is a derivative of gce.py that adds support for filtering
# the returned inventory to only include instances that have tags
# as specified by GCE_TAGGED_INSTANCES. This prevents dynamic 
# inventory for multiple clusters within the same project from
# accidentally stomping each other.

# pylint: skip-file

'''
GCE external inventory script
=================================

Generates inventory that Ansible can understand by making API requests
Google Compute Engine via the libcloud library.  Full install/configuration
instructions for the gce* modules can be found in the comments of
ansible/test/gce_tests.py.

When run against a specific host, this script returns the following variables
based on the data obtained from the libcloud Node object:
 - gce_uuid
 - gce_id
 - gce_image
 - gce_machine_type
 - gce_private_ip
 - gce_public_ip
 - gce_name
 - gce_description
 - gce_status
 - gce_zone
 - gce_tags
 - gce_metadata
 - gce_network

When run in --list mode, instances are grouped by the following categories:
 - zone:
   zone group name examples are us-central1-b, europe-west1-a, etc.
 - instance tags:
   An entry is created for each tag.  For example, if you have two instances
   with a common tag called 'foo', they will both be grouped together under
   the 'tag_foo' name.
 - network name:
   the name of the network is appended to 'network_' (e.g. the 'default'
   network will result in a group named 'network_default')
 - machine type
   types follow a pattern like n1-standard-4, g1-small, etc.
 - running status:
   group name prefixed with 'status_' (e.g. status_running, status_stopped,..)
 - image:
   when using an ephemeral/scratch disk, this will be set to the image name
   used when creating the instance (e.g. debian-7-wheezy-v20130816).  when
   your instance was created with a root persistent disk it will be set to
   'persistent_disk' since there is no current way to determine the image.

Examples:
  Execute uname on all instances in the us-central1-a zone
  $ ansible -i gce.py us-central1-a -m shell -a "/bin/uname -a"

  Use the GCE inventory script to print out instance specific information
  $ contrib/inventory/gce.py --host my_instance

Author: Eric Johnson <erjohnso@google.com>
Contributors: Matt Hite <mhite@hotmail.com>
Version: 0.0.2
'''

__requires__ = ['pycrypto>=2.6']
try:
    import pkg_resources
except ImportError:
    # Use pkg_resources to find the correct versions of libraries and set
    # sys.path appropriately when there are multiversion installs.  We don't
    # fail here as there is code that better expresses the errors where the
    # library is used.
    pass

USER_AGENT_PRODUCT="Ansible-gce_inventory_plugin"
USER_AGENT_VERSION="v2"

import sys
import os
import time
import argparse
import ConfigParser

import logging
logging.getLogger('libcloud.common.google').addHandler(logging.NullHandler())

try:
    import json
except ImportError:
    import simplejson as json

try:
    from libcloud.compute.types import Provider
    from libcloud.compute.providers import get_driver
    from libcloud.common.google import ResourceNotFoundError
    _ = Provider.GCE
except:
    sys.exit("GCE inventory script requires libcloud >= 0.13")


class GceInventory(object):
    def __init__(self):
        # Read settings and parse CLI arguments
        self.parse_cli_args()
        self.config = self.get_config()
        self.driver = self.get_gce_driver()
        self.ip_type = self.get_inventory_options()
        if self.ip_type:
            self.ip_type = self.ip_type.lower()

        # Just display data for specific host
        if self.args.host:
            print(self.json_format_dict(self.node_to_dict(
                    self.get_instance(self.args.host)),
                    pretty=self.args.pretty))
            sys.exit(0)

        zones = self.parse_env_zones()

        # Otherwise, assume user wants all instances grouped
        print(self.json_format_dict(self.group_instances(zones),
            pretty=self.args.pretty))
        sys.exit(0)

    def get_config(self):
        """
        Populates a SafeConfigParser object with defaults and
        attempts to read an .ini-style configuration from the filename
        specified in GCE_INI_PATH. If the environment variable is
        not present, the filename defaults to gce.ini in the current
        working directory.
        """
        gce_ini_default_path = os.path.join(
            os.path.dirname(os.path.realpath(__file__)), "gce.ini")
        gce_ini_path = os.environ.get('GCE_INI_PATH', gce_ini_default_path)

        # Create a ConfigParser.
        # This provides empty defaults to each key, so that environment
        # variable configuration (as opposed to INI configuration) is able
        # to work.
        config = ConfigParser.SafeConfigParser(defaults={
            'gce_service_account_email_address': '',
            'gce_service_account_pem_file_path': '',
            'gce_project_id': '',
            'libcloud_secrets': '',
            'inventory_ip_type': '',
        })
        if 'gce' not in config.sections():
            config.add_section('gce')
        if 'inventory' not in config.sections():
            config.add_section('inventory')

        config.read(gce_ini_path)

        #########
        # Section added for processing ini settings
        #########

        # Set the instance_states filter based on config file options
        self.instance_states = []
        if config.has_option('gce', 'instance_states'):
            states = config.get('gce', 'instance_states')
            # Ignore if instance_states is an empty string.
            if states:
                self.instance_states = states.split(',')

        return config

    def get_inventory_options(self):
        """Determine inventory options. Environment variables always
        take precedence over configuration files."""
        ip_type = self.config.get('inventory', 'inventory_ip_type')
        # If the appropriate environment variables are set, they override
        # other configuration
        ip_type = os.environ.get('INVENTORY_IP_TYPE', ip_type)
        return ip_type

    def get_gce_driver(self):
        """Determine the GCE authorization settings and return a
        libcloud driver.
        """
        # Attempt to get GCE params from a configuration file, if one
        # exists.
        secrets_path = self.config.get('gce', 'libcloud_secrets')
        secrets_found = False
        try:
            import secrets
            args = list(getattr(secrets, 'GCE_PARAMS', []))
            kwargs = getattr(secrets, 'GCE_KEYWORD_PARAMS', {})
            secrets_found = True
        except:
            pass

        if not secrets_found and secrets_path:
            if not secrets_path.endswith('secrets.py'):
                err = "Must specify libcloud secrets file as "
                err += "/absolute/path/to/secrets.py"
                sys.exit(err)
            sys.path.append(os.path.dirname(secrets_path))
            try:
                import secrets
                args = list(getattr(secrets, 'GCE_PARAMS', []))
                kwargs = getattr(secrets, 'GCE_KEYWORD_PARAMS', {})
                secrets_found = True
            except:
                pass
        if not secrets_found:
            args = [
                self.config.get('gce','gce_service_account_email_address'),
                self.config.get('gce','gce_service_account_pem_file_path')
            ]
            kwargs = {'project': self.config.get('gce', 'gce_project_id')}

        # If the appropriate environment variables are set, they override
        # other configuration; process those into our args and kwargs.
        args[0] = os.environ.get('GCE_EMAIL', args[0])
        args[1] = os.environ.get('GCE_PEM_FILE_PATH', args[1])
        kwargs['project'] = os.environ.get('GCE_PROJECT', kwargs['project'])

        # Retrieve and return the GCE driver.
        gce = get_driver(Provider.GCE)(*args, **kwargs)
        gce.connection.user_agent_append(
            '%s/%s' % (USER_AGENT_PRODUCT, USER_AGENT_VERSION),
        )
        return gce

    def parse_env_zones(self):
        '''returns a list of comma seperated zones parsed from the GCE_ZONE environment variable.
        If provided, this will be used to filter the results of the grouped_instances call'''
        import csv
        reader = csv.reader([os.environ.get('GCE_ZONE',"")], skipinitialspace=True)
        zones = [r for r in reader]
        return [z for z in zones[0]]

    def parse_cli_args(self):
        ''' Command line argument processing '''

        parser = argparse.ArgumentParser(
                description='Produce an Ansible Inventory file based on GCE')
        parser.add_argument('--list', action='store_true', default=True,
                           help='List instances (default: True)')
        parser.add_argument('--host', action='store',
                           help='Get all information about an instance')
        parser.add_argument('--tagged', action='store',
                           help='Only include instances with this tag')
        parser.add_argument('--pretty', action='store_true', default=False,
                           help='Pretty format (default: False)')
        self.args = parser.parse_args()

        tag_env = os.environ.get('GCE_TAGGED_INSTANCES')
        if not self.args.tagged and tag_env:
            self.args.tagged = tag_env

    def node_to_dict(self, inst):
        md = {}

        if inst is None:
            return {}

        if inst.extra['metadata'].has_key('items'):
            for entry in inst.extra['metadata']['items']:
                md[entry['key']] = entry['value']

        net = inst.extra['networkInterfaces'][0]['network'].split('/')[-1]
        # default to exernal IP unless user has specified they prefer internal
        if self.ip_type == 'internal':
            ssh_host = inst.private_ips[0]
        else:
            ssh_host = inst.public_ips[0] if len(inst.public_ips) >= 1 else inst.private_ips[0]

        return {
            'gce_uuid': inst.uuid,
            'gce_id': inst.id,
            'gce_image': inst.image,
            'gce_machine_type': inst.size,
            'gce_private_ip': inst.private_ips[0],
            'gce_public_ip': inst.public_ips[0] if len(inst.public_ips) >= 1 else None,
            'gce_name': inst.name,
            'gce_description': inst.extra['description'],
            'gce_status': inst.extra['status'],
            'gce_zone': inst.extra['zone'].name,
            'gce_tags': inst.extra['tags'],
            'gce_metadata': md,
            'gce_network': net,
            # Hosts don't have a public name, so we add an IP
            'ansible_host': ssh_host
        }

    def get_instance(self, instance_name):
        '''Gets details about a specific instance '''
        try:
            return self.driver.ex_get_node(instance_name)
        except Exception as e:
            return None

    def group_instances(self, zones=None):
        '''Group all instances'''
        groups = {}
        meta = {}
        meta["hostvars"] = {}

        # list_nodes will fail if a disk is in the process of being deleted
        # from a node, which is not uncommon if other playbooks are managing
        # the same project. Retry if we receive a not found error.
        nodes = []
        tries = 0
        while True:
            try:
                nodes = self.driver.list_nodes()
                break
            except ResourceNotFoundError:
                tries = tries + 1
                if tries > 15:
                    raise e
                time.sleep(1)
                continue

        for node in nodes:

            # This check filters on the desired instance states defined in the
            # config file with the instance_states config option.
            #
            # If the instance_states list is _empty_ then _ALL_ states are returned.
            #
            # If the instance_states list is _populated_ then check the current
            # state against the instance_states list
            if self.instance_states and not node.extra['status'] in self.instance_states:
                continue

            name = node.name

            if self.args.tagged and self.args.tagged not in node.extra['tags']:
                continue

            meta["hostvars"][name] = self.node_to_dict(node)

            zone = node.extra['zone'].name

            # To avoid making multiple requests per zone
            # we list all nodes and then filter the results
            if zones and zone not in zones:
                continue

            if groups.has_key(zone): groups[zone].append(name)
            else: groups[zone] = [name]

            tags = node.extra['tags']
            for t in tags:
                if t.startswith('group-'):
                    tag = t[6:]
                else:
                    tag = 'tag_%s' % t
                if groups.has_key(tag): groups[tag].append(name)
                else: groups[tag] = [name]

            net = node.extra['networkInterfaces'][0]['network'].split('/')[-1]
            net = 'network_%s' % net
            if groups.has_key(net): groups[net].append(name)
            else: groups[net] = [name]

            machine_type = node.size
            if groups.has_key(machine_type): groups[machine_type].append(name)
            else: groups[machine_type] = [name]

            image = node.image and node.image or 'persistent_disk'
            if groups.has_key(image): groups[image].append(name)
            else: groups[image] = [name]

            status = node.extra['status']
            stat = 'status_%s' % status.lower()
            if groups.has_key(stat): groups[stat].append(name)
            else: groups[stat] = [name]

        groups["_meta"] = meta

        return groups

    def json_format_dict(self, data, pretty=False):
        ''' Converts a dict to a JSON object and dumps it as a formatted
        string '''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)


# Run the script
GceInventory()
