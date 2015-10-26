import os
import unittest
import tempfile
import shutil
import yaml

from ooinstall.oo_config import OOConfig, Host, OOConfigInvalidHostError

SAMPLE_CONFIG = """
variant: openshift-enterprise
ansible_ssh_user: root
hosts:
  - ip: 10.0.0.1
    hostname: master-private.example.com
    public_ip: 24.222.0.1
    public_hostname: master.example.com
    master: true
    node: true
  - ip: 10.0.0.2
    hostname: node1-private.example.com
    public_ip: 24.222.0.2
    public_hostname: node1.example.com
    node: true
  - ip: 10.0.0.3
    hostname: node2-private.example.com
    public_ip: 24.222.0.3
    public_hostname: node2.example.com
    node: true
"""

CONFIG_INCOMPLETE_FACTS = """
hosts:
  - ip: 10.0.0.1
    hostname: master-private.example.com
    public_ip: 24.222.0.1
    public_hostname: master.example.com
    master: true
  - ip: 10.0.0.2
    hostname: node1-private.example.com
    public_ip: 24.222.0.2
    node: true
  - ip: 10.0.0.3
    node: true
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
        f = open(path, 'w')
        f.write(config_str)
        f.close()
        return path


class OOConfigTests(OOInstallFixture):

    def test_load_config(self):

        cfg_path = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), SAMPLE_CONFIG)
        ooconfig = OOConfig(cfg_path)

        self.assertEquals(3, len(ooconfig.hosts))
        self.assertEquals("10.0.0.1", ooconfig.hosts[0].name)
        self.assertEquals("10.0.0.1", ooconfig.hosts[0].ip)
        self.assertEquals("master-private.example.com", ooconfig.hosts[0].hostname)

        self.assertEquals(["10.0.0.1", "10.0.0.2", "10.0.0.3"],
                          [host['ip'] for host in ooconfig.settings['hosts']])

        self.assertEquals('openshift-enterprise', ooconfig.settings['variant'])

    def test_load_complete_validated_facts(self):
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

        self.assertEquals(3, len(written_config['hosts']))
        for h in written_config['hosts']:
            self.assertTrue('ip' in h)
            self.assertTrue('public_ip' in h)
            self.assertTrue('hostname' in h)
            self.assertTrue('public_hostname' in h)

        self.assertTrue('ansible_ssh_user' in written_config)
        self.assertTrue('variant' in written_config)

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




