import os
import unittest
import tempfile
import shutil

from six.moves import configparser

from ooinstall import openshift_ansible
from ooinstall.oo_config import Host, OOConfig


BASE_CONFIG = """
---
variant: openshift-enterprise
variant_version: 3.3
version: v2
deployment:
    ansible_ssh_user: cloud-user
    hosts: []
    roles:
        master:
        node:
"""


class TestOpenShiftAnsible(unittest.TestCase):

    def setUp(self):
        self.tempfiles = []
        self.work_dir = tempfile.mkdtemp(prefix='openshift_ansible_tests')
        self.configfile = os.path.join(self.work_dir, 'ooinstall.config')
        with open(self.configfile, 'w') as config_file:
            config_file.write(BASE_CONFIG)
        self.inventory = os.path.join(self.work_dir, 'hosts')
        config = OOConfig(self.configfile)
        config.settings['ansible_inventory_path'] = self.inventory
        openshift_ansible.set_config(config)

    def tearDown(self):
        shutil.rmtree(self.work_dir)

    def test_generate_inventory_new_nodes(self):
        hosts = generate_hosts(1, 'master', roles=(['master', 'etcd']))
        hosts.extend(generate_hosts(1, 'node', roles=['node']))
        hosts.extend(generate_hosts(1, 'new_node', roles=['node'], new_host=True))
        openshift_ansible.generate_inventory(hosts)
        inventory = configparser.ConfigParser(allow_no_value=True)
        inventory.read(self.inventory)
        self.assertTrue(inventory.has_section('new_nodes'))
        self.assertTrue(inventory.has_option('new_nodes', 'new_node1'))

    def test_write_inventory_vars_role_vars(self):
        with open(self.inventory, 'w') as inv:
            openshift_ansible.CFG.deployment.roles['master'].variables = {'color': 'blue'}
            openshift_ansible.CFG.deployment.roles['node'].variables = {'color': 'green'}
            openshift_ansible.write_inventory_vars(inv, None)

        inventory = configparser.ConfigParser(allow_no_value=True)
        inventory.read(self.inventory)
        self.assertTrue(inventory.has_section('masters:vars'))
        self.assertEquals('blue', inventory.get('masters:vars', 'color'))
        self.assertTrue(inventory.has_section('nodes:vars'))
        self.assertEquals('green', inventory.get('nodes:vars', 'color'))


def generate_hosts(num_hosts, name_prefix, roles=None, new_host=False):
    hosts = []
    for num in range(1, num_hosts + 1):
        hosts.append(Host(connect_to=name_prefix + str(num),
                          roles=roles, new_host=new_host))
    return hosts
