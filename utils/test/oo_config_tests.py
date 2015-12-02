# TODO: Temporarily disabled due to importing old code into openshift-ansible
# repo. We will work on these over time.
# pylint: disable=bad-continuation,missing-docstring,no-self-use,invalid-name

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
  - connect_to: master-private.example.com
    ip: 10.0.0.1
    hostname: master-private.example.com
    public_ip: 24.222.0.1
    public_hostname: master.example.com
    master: true
    node: true
  - connect_to: node1-private.example.com
    ip: 10.0.0.2
    hostname: node1-private.example.com
    public_ip: 24.222.0.2
    public_hostname: node1.example.com
    node: true
  - connect_to: node2-private.example.com
    ip: 10.0.0.3
    hostname: node2-private.example.com
    public_ip: 24.222.0.3
    public_hostname: node2.example.com
    node: true
"""

# Used to test automatic upgrading of config:
LEGACY_CONFIG = """
Description: This is the configuration file for the OpenShift Ansible-Based Installer.
Name: OpenShift Ansible-Based Installer Configuration
Subscription: {type: none}
Vendor: OpenShift Community
Version: 0.0.1
ansible_config: /tmp/notreal/ansible.cfg
ansible_inventory_directory: /tmp/notreal/.config/openshift/.ansible
ansible_log_path: /tmp/ansible.log
ansible_plugins_directory: /tmp/notreal/.python-eggs/ooinstall-3.0.0-py2.7.egg-tmp/ooinstall/ansible_plugins
masters: [10.0.0.1]
nodes: [10.0.0.2, 10.0.0.3]
validated_facts:
  10.0.0.1: {hostname: master-private.example.com, ip: 10.0.0.1, public_hostname: master.example.com, public_ip: 24.222.0.1}
  10.0.0.2: {hostname: node1-private.example.com, ip: 10.0.0.2, public_hostname: node1.example.com, public_ip: 24.222.0.2}
  10.0.0.3: {hostname: node2-private.example.com, ip: 10.0.0.3, public_hostname: node2.example.com, public_ip: 24.222.0.3}
"""


CONFIG_INCOMPLETE_FACTS = """
hosts:
  - connect_to: 10.0.0.1
    ip: 10.0.0.1
    hostname: master-private.example.com
    public_ip: 24.222.0.1
    public_hostname: master.example.com
    master: true
  - connect_to: 10.0.0.2
    ip: 10.0.0.2
    hostname: 24.222.0.2
    public_ip: 24.222.0.2
    node: true
  - connect_to: 10.0.0.3
    ip: 10.0.0.3
    node: true
"""

CONFIG_BAD = """
variant: openshift-enterprise
ansible_ssh_user: root
hosts:
  - connect_to: master-private.example.com
    ip: 10.0.0.1
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
  - connect_to: node2-private.example.com
    ip: 10.0.0.3
    hostname: node2-private.example.com
    public_ip: 24.222.0.3
    public_hostname: node2.example.com
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
        cfg_file = open(path, 'w')
        cfg_file.write(config_str)
        cfg_file.close()
        return path


class LegacyOOConfigTests(OOInstallFixture):

    def setUp(self):
        OOInstallFixture.setUp(self)
        self.cfg_path = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), LEGACY_CONFIG)
        self.cfg = OOConfig(self.cfg_path)

    def test_load_config_memory(self):
        self.assertEquals('openshift-enterprise', self.cfg.settings['variant'])
        self.assertEquals('3.0', self.cfg.settings['variant_version'])
        self.assertEquals('v1', self.cfg.settings['version'])

        self.assertEquals(3, len(self.cfg.hosts))
        h1 = self.cfg.get_host('10.0.0.1')
        self.assertEquals('10.0.0.1', h1.ip)
        self.assertEquals('24.222.0.1', h1.public_ip)
        self.assertEquals('master-private.example.com', h1.hostname)
        self.assertEquals('master.example.com', h1.public_hostname)

        h2 = self.cfg.get_host('10.0.0.2')
        self.assertEquals('10.0.0.2', h2.ip)
        self.assertEquals('24.222.0.2', h2.public_ip)
        self.assertEquals('node1-private.example.com', h2.hostname)
        self.assertEquals('node1.example.com', h2.public_hostname)

        h3 = self.cfg.get_host('10.0.0.3')
        self.assertEquals('10.0.0.3', h3.ip)
        self.assertEquals('24.222.0.3', h3.public_ip)
        self.assertEquals('node2-private.example.com', h3.hostname)
        self.assertEquals('node2.example.com', h3.public_hostname)

        self.assertFalse('masters' in self.cfg.settings)
        self.assertFalse('nodes' in self.cfg.settings)
        self.assertFalse('Description' in self.cfg.settings)
        self.assertFalse('Name' in self.cfg.settings)
        self.assertFalse('Subscription' in self.cfg.settings)
        self.assertFalse('Vendor' in self.cfg.settings)
        self.assertFalse('Version' in self.cfg.settings)
        self.assertFalse('validates_facts' in self.cfg.settings)


class OOConfigTests(OOInstallFixture):

    def test_load_config(self):

        cfg_path = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), SAMPLE_CONFIG)
        ooconfig = OOConfig(cfg_path)

        self.assertEquals(3, len(ooconfig.hosts))
        self.assertEquals("master-private.example.com", ooconfig.hosts[0].connect_to)
        self.assertEquals("10.0.0.1", ooconfig.hosts[0].ip)
        self.assertEquals("master-private.example.com", ooconfig.hosts[0].hostname)

        self.assertEquals(["10.0.0.1", "10.0.0.2", "10.0.0.3"],
                          [host['ip'] for host in ooconfig.settings['hosts']])

        self.assertEquals('openshift-enterprise', ooconfig.settings['variant'])
        self.assertEquals('v1', ooconfig.settings['version'])

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

        self.assertEquals(3, len(written_config['hosts']))
        for h in written_config['hosts']:
            self.assertTrue('ip' in h)
            self.assertTrue('public_ip' in h)
            self.assertTrue('hostname' in h)
            self.assertTrue('public_hostname' in h)

        self.assertTrue('ansible_ssh_user' in written_config)
        self.assertTrue('variant' in written_config)
        self.assertEquals('v1', written_config['version'])

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




