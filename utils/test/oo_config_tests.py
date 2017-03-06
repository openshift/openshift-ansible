# TODO: Temporarily disabled due to importing old code into openshift-ansible
# repo. We will work on these over time.
# pylint: disable=bad-continuation,missing-docstring,no-self-use,invalid-name

import os
import unittest
import tempfile
import shutil
import yaml

from six.moves import cStringIO

from ooinstall.oo_config import OOConfig, Host, OOConfigInvalidHostError
import ooinstall.openshift_ansible

SAMPLE_CONFIG = """
variant: openshift-enterprise
variant_version: 3.3
version: v2
deployment:
    ansible_ssh_user: root
    hosts:
      - connect_to: master-private.example.com
        ip: 10.0.0.1
        hostname: master-private.example.com
        public_ip: 24.222.0.1
        public_hostname: master.example.com
        roles:
            - master
            - node
      - connect_to: node1-private.example.com
        ip: 10.0.0.2
        hostname: node1-private.example.com
        public_ip: 24.222.0.2
        public_hostname: node1.example.com
        roles:
            - node
      - connect_to: node2-private.example.com
        ip: 10.0.0.3
        hostname: node2-private.example.com
        public_ip: 24.222.0.3
        public_hostname: node2.example.com
        roles:
            - node
    roles:
        master:
        node:
"""


CONFIG_INCOMPLETE_FACTS = """
version: v2
deployment:
    ansible_ssh_user: root
    hosts:
      - connect_to: 10.0.0.1
        ip: 10.0.0.1
        hostname: master-private.example.com
        public_ip: 24.222.0.1
        public_hostname: master.example.com
        roles:
            - master
      - connect_to: 10.0.0.2
        ip: 10.0.0.2
        hostname: 24.222.0.2
        public_ip: 24.222.0.2
        roles:
            - node
      - connect_to: 10.0.0.3
        ip: 10.0.0.3
        roles:
            - node
    roles:
        master:
        node:
"""

CONFIG_BAD = """
variant: openshift-enterprise
version: v2
deployment:
    ansible_ssh_user: root
    hosts:
      - connect_to: master-private.example.com
        ip: 10.0.0.1
        hostname: master-private.example.com
        public_ip: 24.222.0.1
        public_hostname: master.example.com
        roles:
            - master
            - node
      - ip: 10.0.0.2
        hostname: node1-private.example.com
        public_ip: 24.222.0.2
        public_hostname: node1.example.com
        roles:
            - node
      - connect_to: node2-private.example.com
        ip: 10.0.0.3
        hostname: node2-private.example.com
        public_ip: 24.222.0.3
        public_hostname: node2.example.com
        roles:
            - node
    roles:
        master:
        node:
"""

class OOInstallFixture(unittest.TestCase):

    def setUp(self):
        self.tempfiles = []
        self.work_dir = tempfile.mkdtemp(prefix='ooconfigtests')
        self.tempfiles.append(self.work_dir)

    def tearDown(self):
        for path in self.tempfiles:
            if os.path.isdir(path):
                shutil.rmtree(path)
            else:
                os.remove(path)

    def write_config(self, path, config_str):
        """
        Write given config to a temporary file which will be cleaned
        up in teardown.
        Returns full path to the file.
        """
        cfg_file = open(path, 'w')
        cfg_file.write(config_str)
        cfg_file.close()
        return path



class OOConfigTests(OOInstallFixture):

    def test_load_config(self):

        cfg_path = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), SAMPLE_CONFIG)
        ooconfig = OOConfig(cfg_path)

        self.assertEquals(3, len(ooconfig.deployment.hosts))
        self.assertEquals("master-private.example.com", ooconfig.deployment.hosts[0].connect_to)
        self.assertEquals("10.0.0.1", ooconfig.deployment.hosts[0].ip)
        self.assertEquals("master-private.example.com", ooconfig.deployment.hosts[0].hostname)

        self.assertEquals(["10.0.0.1", "10.0.0.2", "10.0.0.3"],
                          [host.ip for host in ooconfig.deployment.hosts])

        self.assertEquals('openshift-enterprise', ooconfig.settings['variant'])
        self.assertEquals('v2', ooconfig.settings['version'])

    def test_load_bad_config(self):

        cfg_path = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), CONFIG_BAD)
        try:
            OOConfig(cfg_path)
            assert False
        except OOConfigInvalidHostError:
            assert True


    def test_load_complete_facts(self):
        cfg_path = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), SAMPLE_CONFIG)
        ooconfig = OOConfig(cfg_path)
        missing_host_facts = ooconfig.calc_missing_facts()
        self.assertEquals(0, len(missing_host_facts))

    # Test missing optional facts the user must confirm:
    def test_load_host_incomplete_facts(self):
        cfg_path = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), CONFIG_INCOMPLETE_FACTS)
        ooconfig = OOConfig(cfg_path)
        missing_host_facts = ooconfig.calc_missing_facts()
        self.assertEquals(2, len(missing_host_facts))
        self.assertEquals(1, len(missing_host_facts['10.0.0.2']))
        self.assertEquals(3, len(missing_host_facts['10.0.0.3']))

    def test_write_config(self):
        cfg_path = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), SAMPLE_CONFIG)
        ooconfig = OOConfig(cfg_path)
        ooconfig.save_to_disk()

        f = open(cfg_path, 'r')
        written_config = yaml.safe_load(f.read())
        f.close()



        self.assertEquals(3, len(written_config['deployment']['hosts']))
        for h in written_config['deployment']['hosts']:
            self.assertTrue('ip' in h)
            self.assertTrue('public_ip' in h)
            self.assertTrue('hostname' in h)
            self.assertTrue('public_hostname' in h)

        self.assertTrue('ansible_ssh_user' in written_config['deployment'])
        self.assertTrue('variant' in written_config)
        self.assertEquals('v2', written_config['version'])

        # Some advanced settings should not get written out if they
        # were not specified by the user:
        self.assertFalse('ansible_inventory_directory' in written_config)


class HostTests(OOInstallFixture):

    def test_load_host_no_ip_or_hostname(self):
        yaml_props = {
            'public_ip': '192.168.0.1',
            'public_hostname': 'a.example.com',
            'master': True
        }
        self.assertRaises(OOConfigInvalidHostError, Host, **yaml_props)

    def test_load_host_no_master_or_node_specified(self):
        yaml_props = {
            'ip': '192.168.0.1',
            'hostname': 'a.example.com',
            'public_ip': '192.168.0.1',
            'public_hostname': 'a.example.com',
        }
        self.assertRaises(OOConfigInvalidHostError, Host, **yaml_props)

    def test_inventory_file_quotes_node_labels(self):
        """Verify a host entry wraps openshift_node_labels value in double quotes"""
        yaml_props = {
            'ip': '192.168.0.1',
            'hostname': 'a.example.com',
            'connect_to': 'a-private.example.com',
            'public_ip': '192.168.0.1',
            'public_hostname': 'a.example.com',
            'new_host': True,
            'roles': ['node'],
            'node_labels': {
                'region': 'infra'
            },

        }

        new_node = Host(**yaml_props)
        inventory = cStringIO()
        # This is what the 'write_host' function generates. write_host
        # has no return value, it just writes directly to the file
        # 'inventory' which in this test-case is a StringIO object
        ooinstall.openshift_ansible.write_host(
            new_node,
            'node',
            inventory,
            schedulable=True)
        # read the value of what was written to the inventory "file"
        legacy_inventory_line = inventory.getvalue()

        # Given the `yaml_props` above we should see a line like this:
        #     openshift_node_labels="{'region': 'infra'}"
        node_labels_expected = '''openshift_node_labels="{'region': 'infra'}"'''  # Quotes around the hash
        node_labels_bad = '''openshift_node_labels={'region': 'infra'}'''  # No quotes around the hash

        # The good line is present in the written inventory line
        self.assertIn(node_labels_expected, legacy_inventory_line)
        # An unquoted version is not present
        self.assertNotIn(node_labels_bad, legacy_inventory_line)
