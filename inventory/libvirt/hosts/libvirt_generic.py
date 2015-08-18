#!/usr/bin/env python2

'''
libvirt external inventory script
=================================

Ansible has a feature where instead of reading from /etc/ansible/hosts
as a text file, it can query external programs to obtain the list
of hosts, groups the hosts are in, and even variables to assign to each host.

To use this, copy this file over /etc/ansible/hosts and chmod +x the file.
This, more or less, allows you to keep one central database containing
info about all of your managed instances.

'''

# (c) 2015, Jason DeTiberus <jdetiber@redhat.com>
#
# This file is part of Ansible,
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

######################################################################

import argparse
import ConfigParser
import os
import sys
import libvirt
import xml.etree.ElementTree as ET

try:
    import json
except ImportError:
    import simplejson as json


class LibvirtInventory(object):
    ''' libvirt dynamic inventory '''

    def __init__(self):
        ''' Main execution path '''

        self.inventory = dict()  # A list of groups and the hosts in that group
        self.cache = dict()  # Details about hosts in the inventory

        # Read settings and parse CLI arguments
        self.read_settings()
        self.parse_cli_args()

        if self.args.host:
            print _json_format_dict(self.get_host_info(), self.args.pretty)
        elif self.args.list:
            print _json_format_dict(self.get_inventory(), self.args.pretty)
        else:  # default action with no options
            print _json_format_dict(self.get_inventory(), self.args.pretty)

    def read_settings(self):
        ''' Reads the settings from the libvirt.ini file '''

        config = ConfigParser.SafeConfigParser()
        config.read(
            os.path.dirname(os.path.realpath(__file__)) + '/libvirt.ini'
        )
        self.libvirt_uri = config.get('libvirt', 'uri')

    def parse_cli_args(self):
        ''' Command line argument processing '''

        parser = argparse.ArgumentParser(
            description='Produce an Ansible Inventory file based on libvirt'
        )
        parser.add_argument(
            '--list',
            action='store_true',
            default=True,
            help='List instances (default: True)'
        )
        parser.add_argument(
            '--host',
            action='store',
            help='Get all the variables about a specific instance'
        )
        parser.add_argument(
            '--pretty',
            action='store_true',
            default=False,
            help='Pretty format (default: False)'
        )
        self.args = parser.parse_args()

    def get_host_info(self):
        ''' Get variables about a specific host '''

        inventory = self.get_inventory()
        if self.args.host in inventory['_meta']['hostvars']:
            return inventory['_meta']['hostvars'][self.args.host]

    def get_inventory(self):
        ''' Construct the inventory '''

        inventory = dict(_meta=dict(hostvars=dict()))

        conn = libvirt.openReadOnly(self.libvirt_uri)
        if conn is None:
            print "Failed to open connection to %s" % self.libvirt_uri
            sys.exit(1)

        domains = conn.listAllDomains()
        if domains is None:
            print "Failed to list domains for connection %s" % self.libvirt_uri
            sys.exit(1)

        for domain in domains:
            hostvars = dict(libvirt_name=domain.name(),
                            libvirt_id=domain.ID(),
                            libvirt_uuid=domain.UUIDString())
            domain_name = domain.name()

            # TODO: add support for guests that are not in a running state
            state, _ = domain.state()
            # 2 is the state for a running guest
            if state != 1:
                continue

            hostvars['libvirt_status'] = 'running'

            root = ET.fromstring(domain.XMLDesc())
            ansible_ns = {'ansible': 'https://github.com/ansible/ansible'}
            for tag_elem in root.findall('./metadata/ansible:tags/ansible:tag', ansible_ns):
                tag = tag_elem.text
                _push(inventory, "tag_%s" % tag, domain_name)
                _push(hostvars, 'libvirt_tags', tag)

            # TODO: support more than one network interface, also support
            # interface types other than 'network'
            interface = root.find("./devices/interface[@type='network']")
            if interface is not None:
                source_elem = interface.find('source')
                mac_elem = interface.find('mac')
                if source_elem is not None and \
                   mac_elem    is not None:
                    # Adding this to disable pylint check specifically
                    # ignoring libvirt-python versions that
                    # do not include DHCPLeases
                    # This is needed until we upgrade the build bot to
                    # RHEL7 (>= 1.2.6 libvirt)
                    # pylint: disable=no-member
                    dhcp_leases = conn.networkLookupByName(source_elem.get('network')) \
                                      .DHCPLeases(mac_elem.get('address'))
                    if len(dhcp_leases) > 0:
                        ip_address = dhcp_leases[0]['ipaddr']
                        hostvars['ansible_ssh_host'] = ip_address
                        hostvars['libvirt_ip_address'] = ip_address

            inventory['_meta']['hostvars'][domain_name] = hostvars

        return inventory

def _push(my_dict, key, element):
    '''
    Push element to the my_dict[key] list.
    After having initialized my_dict[key] if it dosn't exist.
    '''

    if key in my_dict:
        my_dict[key].append(element)
    else:
        my_dict[key] = [element]

def _json_format_dict(data, pretty=False):
    ''' Serialize data to a JSON formated str '''

    if pretty:
        return json.dumps(data, sort_keys=True, indent=2)
    else:
        return json.dumps(data)

LibvirtInventory()
