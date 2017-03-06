# TODO: Temporarily disabled due to importing old code into openshift-ansible
# repo. We will work on these over time.
# pylint: disable=bad-continuation,missing-docstring,no-self-use,invalid-name,too-many-lines

import copy
import os

from six.moves import configparser

import ooinstall.cli_installer as cli

from test.fixture import OOCliFixture, SAMPLE_CONFIG, build_input, read_yaml
from mock import patch


MOCK_FACTS = {
    '10.0.0.1': {
        'common': {
            'ip': '10.0.0.1',
            'public_ip': '10.0.0.1',
            'hostname': 'master-private.example.com',
            'public_hostname': 'master.example.com'
        }
    },
    '10.0.0.2': {
        'common': {
            'ip': '10.0.0.2',
            'public_ip': '10.0.0.2',
            'hostname': 'node1-private.example.com',
            'public_hostname': 'node1.example.com'
        }
    },
    '10.0.0.3': {
        'common': {
            'ip': '10.0.0.3',
            'public_ip': '10.0.0.3',
            'hostname': 'node2-private.example.com',
            'public_hostname': 'node2.example.com'
        }
    },
    '10.1.0.1': {
        'common': {
            'ip': '10.1.0.1',
            'public_ip': '10.1.0.1',
            'hostname': 'storage-private.example.com',
            'public_hostname': 'storage.example.com'
        }
    },
}

MOCK_FACTS_QUICKHA = {
    '10.0.0.1': {
        'common': {
            'ip': '10.0.0.1',
            'public_ip': '10.0.0.1',
            'hostname': 'master-private.example.com',
            'public_hostname': 'master.example.com'
        }
    },
    '10.0.0.2': {
        'common': {
            'ip': '10.0.0.2',
            'public_ip': '10.0.0.2',
            'hostname': 'node1-private.example.com',
            'public_hostname': 'node1.example.com'
        }
    },
    '10.0.0.3': {
        'common': {
            'ip': '10.0.0.3',
            'public_ip': '10.0.0.3',
            'hostname': 'node2-private.example.com',
            'public_hostname': 'node2.example.com'
        }
    },
    '10.0.0.4': {
        'common': {
            'ip': '10.0.0.4',
            'public_ip': '10.0.0.4',
            'hostname': 'node3-private.example.com',
            'public_hostname': 'node3.example.com'
        }
    },
    '10.0.0.5': {
        'common': {
            'ip': '10.0.0.5',
            'public_ip': '10.0.0.5',
            'hostname': 'proxy-private.example.com',
            'public_hostname': 'proxy.example.com'
        }
    },
    '10.1.0.1': {
        'common': {
            'ip': '10.1.0.1',
            'public_ip': '10.1.0.1',
            'hostname': 'storage-private.example.com',
            'public_hostname': 'storage.example.com'
        }
    },
}

# Missing connect_to on some hosts:
BAD_CONFIG = """
variant: %s
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
            - node
      - ip: 10.0.0.2
        hostname: node1-private.example.com
        public_ip: 24.222.0.2
        public_hostname: node1.example.com
        roles:
            - node
      - connect_to: 10.0.0.3
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

QUICKHA_CONFIG = """
variant: %s
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
            - node
      - connect_to: 10.0.0.2
        ip: 10.0.0.2
        hostname: node1-private.example.com
        public_ip: 24.222.0.2
        public_hostname: node1.example.com
        roles:
            - master
            - node
      - connect_to: 10.0.0.3
        ip: 10.0.0.3
        hostname: node2-private.example.com
        public_ip: 24.222.0.3
        public_hostname: node2.example.com
        roles:
            - master
            - node
      - connect_to: 10.0.0.4
        ip: 10.0.0.4
        hostname: node3-private.example.com
        public_ip: 24.222.0.4
        public_hostname: node3.example.com
        roles:
            - node
      - connect_to: 10.0.0.5
        ip: 10.0.0.5
        hostname: proxy-private.example.com
        public_ip: 24.222.0.5
        public_hostname: proxy.example.com
        roles:
            - master_lb
      - connect_to: 10.1.0.1
        ip: 10.1.0.1
        hostname: storage-private.example.com
        public_ip: 24.222.0.6
        public_hostname: storage.example.com
        roles:
            - storage
    roles:
        master:
        master_lb:
        node:
        storage:
"""

QUICKHA_2_MASTER_CONFIG = """
variant: %s
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
            - node
      - connect_to: 10.0.0.2
        ip: 10.0.0.2
        hostname: node1-private.example.com
        public_ip: 24.222.0.2
        public_hostname: node1.example.com
        roles:
            - master
            - node
      - connect_to: 10.0.0.4
        ip: 10.0.0.4
        hostname: node3-private.example.com
        public_ip: 24.222.0.4
        public_hostname: node3.example.com
        roles:
            - node
      - connect_to: 10.0.0.5
        ip: 10.0.0.5
        hostname: proxy-private.example.com
        public_ip: 24.222.0.5
        public_hostname: proxy.example.com
        roles:
            - master_lb
      - connect_to: 10.1.0.1
        ip: 10.1.0.1
        hostname: storage-private.example.com
        public_ip: 24.222.0.6
        public_hostname: storage.example.com
        roles:
            - storage
    roles:
        master:
        master_lb:
        node:
        storage:
"""

QUICKHA_CONFIG_REUSED_LB = """
variant: %s
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
            - node
      - connect_to: 10.0.0.2
        ip: 10.0.0.2
        hostname: node1-private.example.com
        public_ip: 24.222.0.2
        public_hostname: node1.example.com
        roles:
            - master
            - node
            - master_lb
      - connect_to: 10.0.0.3
        ip: 10.0.0.3
        hostname: node2-private.example.com
        public_ip: 24.222.0.3
        public_hostname: node2.example.com
        roles:
            - master
            - node
      - connect_to: 10.1.0.1
        ip: 10.1.0.1
        hostname: storage-private.example.com
        public_ip: 24.222.0.6
        public_hostname: storage.example.com
        roles:
            - storage
    roles:
        master:
        node:
        storage:
"""

QUICKHA_CONFIG_NO_LB = """
variant: %s
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
            - node
      - connect_to: 10.0.0.2
        ip: 10.0.0.2
        hostname: node1-private.example.com
        public_ip: 24.222.0.2
        public_hostname: node1.example.com
        roles:
            - master
            - node
      - connect_to: 10.0.0.3
        ip: 10.0.0.3
        hostname: node2-private.example.com
        public_ip: 24.222.0.3
        public_hostname: node2.example.com
        roles:
            - master
            - node
      - connect_to: 10.1.0.1
        ip: 10.1.0.1
        hostname: storage-private.example.com
        public_ip: 24.222.0.6
        public_hostname: storage.example.com
        roles:
            - storage
    roles:
        master:
        node:
        storage:
"""

QUICKHA_CONFIG_PRECONFIGURED_LB = """
variant: %s
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
            - node
      - connect_to: 10.0.0.2
        ip: 10.0.0.2
        hostname: node1-private.example.com
        public_ip: 24.222.0.2
        public_hostname: node1.example.com
        roles:
            - master
            - node
      - connect_to: 10.0.0.3
        ip: 10.0.0.3
        hostname: node2-private.example.com
        public_ip: 24.222.0.3
        public_hostname: node2.example.com
        roles:
            - master
            - node
      - connect_to: 10.0.0.4
        ip: 10.0.0.4
        hostname: node3-private.example.com
        public_ip: 24.222.0.4
        public_hostname: node3.example.com
        roles:
            - node
      - connect_to: proxy-private.example.com
        hostname: proxy-private.example.com
        public_hostname: proxy.example.com
        preconfigured: true
        roles:
            - master_lb
      - connect_to: 10.1.0.1
        ip: 10.1.0.1
        hostname: storage-private.example.com
        public_ip: 24.222.0.6
        public_hostname: storage.example.com
        roles:
            - storage
    roles:
        master:
        master_lb:
        node:
        storage:
"""

class UnattendedCliTests(OOCliFixture):

    def setUp(self):
        OOCliFixture.setUp(self)
        self.cli_args.append("-u")

    # unattended with config file and all installed hosts (without --force)
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_get_hosts_to_run_on1(self, load_facts_mock, run_playbook_mock):
        mock_facts = copy.deepcopy(MOCK_FACTS)
        mock_facts['10.0.0.1']['common']['version'] = "3.0.0"
        mock_facts['10.0.0.2']['common']['version'] = "3.0.0"
        mock_facts['10.0.0.3']['common']['version'] = "3.0.0"

        load_facts_mock.return_value = (mock_facts, 0)
        run_playbook_mock.return_value = 0

        config_file = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), SAMPLE_CONFIG % 'openshift-enterprise')

        self.cli_args.extend(["-c", config_file, "install"])
        result = self.runner.invoke(cli.cli, self.cli_args)

        if result.exception is None or result.exit_code != 1:
            self.fail("Unexpected CLI return. Exit code: %s" % result.exit_code)

    # unattended with config file and all installed hosts (with --force)
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_get_hosts_to_run_on2(self, load_facts_mock, run_playbook_mock):
        mock_facts = copy.deepcopy(MOCK_FACTS)
        mock_facts['10.0.0.1']['common']['version'] = "3.0.0"
        mock_facts['10.0.0.2']['common']['version'] = "3.0.0"
        mock_facts['10.0.0.3']['common']['version'] = "3.0.0"
        self._verify_get_hosts_to_run_on(mock_facts, load_facts_mock, run_playbook_mock,
                                         cli_input=None,
                                         exp_hosts_len=3,
                                         exp_hosts_to_run_on_len=3,
                                         force=True)

    # unattended with config file and no installed hosts (without --force)
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_get_hosts_to_run_on3(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0
        self._verify_get_hosts_to_run_on(MOCK_FACTS, load_facts_mock, run_playbook_mock,
                                         cli_input=None,
                                         exp_hosts_len=3,
                                         exp_hosts_to_run_on_len=3,
                                         force=False)

    # unattended with config file and no installed hosts (with --force)
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_get_hosts_to_run_on4(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0
        self._verify_get_hosts_to_run_on(MOCK_FACTS, load_facts_mock, run_playbook_mock,
                                         cli_input=None,
                                         exp_hosts_len=3,
                                         exp_hosts_to_run_on_len=3,
                                         force=True)

    # unattended with config file and some installed some uninstalled hosts (without --force)
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_get_hosts_to_run_on5(self, load_facts_mock, run_playbook_mock):
        mock_facts = copy.deepcopy(MOCK_FACTS)
        mock_facts['10.0.0.1']['common']['version'] = "3.0.0"
        mock_facts['10.0.0.2']['common']['version'] = "3.0.0"
        self._verify_get_hosts_to_run_on(mock_facts, load_facts_mock, run_playbook_mock,
                                         cli_input=None,
                                         exp_hosts_len=3,
                                         exp_hosts_to_run_on_len=2,
                                         force=False)

    # unattended with config file and some installed some uninstalled hosts (with --force)
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_get_hosts_to_run_on6(self, load_facts_mock, run_playbook_mock):
        mock_facts = copy.deepcopy(MOCK_FACTS)
        mock_facts['10.0.0.1']['common']['version'] = "3.0.0"
        mock_facts['10.0.0.2']['common']['version'] = "3.0.0"
        self._verify_get_hosts_to_run_on(mock_facts, load_facts_mock, run_playbook_mock,
                                         cli_input=None,
                                         exp_hosts_len=3,
                                         exp_hosts_to_run_on_len=3,
                                         force=True)

    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_cfg_full_run(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0

        config_file = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), SAMPLE_CONFIG % 'openshift-enterprise')

        self.cli_args.extend(["-c", config_file, "install"])
        result = self.runner.invoke(cli.cli, self.cli_args)
        self.assert_result(result, 0)

        load_facts_args = load_facts_mock.call_args[0]
        self.assertEquals(os.path.join(self.work_dir, "hosts"),
            load_facts_args[0])
        self.assertEquals(os.path.join(self.work_dir,
            "playbooks/byo/openshift_facts.yml"), load_facts_args[1])
        env_vars = load_facts_args[2]
        self.assertEquals(os.path.join(self.work_dir,
            '.ansible/callback_facts.yaml'),
            env_vars['OO_INSTALL_CALLBACK_FACTS_YAML'])
        self.assertEqual('/tmp/ansible.log', env_vars['ANSIBLE_LOG_PATH'])
        # If user running test has rpm installed, this might be set to default:
        self.assertTrue('ANSIBLE_CONFIG' not in env_vars or
            env_vars['ANSIBLE_CONFIG'] == cli.DEFAULT_ANSIBLE_CONFIG)

        # Make sure we ran on the expected masters and nodes:
        hosts = run_playbook_mock.call_args[0][1]
        hosts_to_run_on = run_playbook_mock.call_args[0][2]
        self.assertEquals(3, len(hosts))
        self.assertEquals(3, len(hosts_to_run_on))

    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_inventory_write(self, load_facts_mock, run_playbook_mock):
        merged_config = SAMPLE_CONFIG % 'openshift-enterprise'
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0

        config_file = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), merged_config)

        self.cli_args.extend(["-c", config_file, "install"])
        result = self.runner.invoke(cli.cli, self.cli_args)
        self.assert_result(result, 0)

        # Check the inventory file looks as we would expect:
        inventory = configparser.ConfigParser(allow_no_value=True)
        inventory.read(os.path.join(self.work_dir, 'hosts'))
        self.assertEquals('root',
            inventory.get('OSEv3:vars', 'ansible_ssh_user'))
        self.assertEquals('openshift-enterprise',
            inventory.get('OSEv3:vars', 'deployment_type'))

        # Check the masters:
        self.assertEquals(1, len(inventory.items('masters')))
        self.assertEquals(3, len(inventory.items('nodes')))

        for item in inventory.items('masters'):
            # ansible host lines do NOT parse nicely:
            master_line = item[0]
            if item[1] is not None:
                master_line = "%s=%s" % (master_line, item[1])
            self.assertTrue('openshift_ip' in master_line)
            self.assertTrue('openshift_public_ip' in master_line)
            self.assertTrue('openshift_hostname' in master_line)
            self.assertTrue('openshift_public_hostname' in master_line)

    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_variant_version_latest_assumed(self, load_facts_mock,
        run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0

        config_file = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), SAMPLE_CONFIG % 'openshift-enterprise')

        self.cli_args.extend(["-c", config_file, "install"])
        result = self.runner.invoke(cli.cli, self.cli_args)
        self.assert_result(result, 0)

        written_config = read_yaml(config_file)

        self.assertEquals('openshift-enterprise', written_config['variant'])
        # We didn't specify a version so the latest should have been assumed,
        # and written to disk:
        self.assertEquals('3.3', written_config['variant_version'])

        # Make sure the correct value was passed to ansible:
        inventory = configparser.ConfigParser(allow_no_value=True)
        inventory.read(os.path.join(self.work_dir, 'hosts'))
        self.assertEquals('openshift-enterprise',
            inventory.get('OSEv3:vars', 'deployment_type'))

    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_variant_version_preserved(self, load_facts_mock,
        run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0

        config = SAMPLE_CONFIG % 'openshift-enterprise'
        config = '%s\n%s' % (config, 'variant_version: 3.3')
        config_file = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), config)

        self.cli_args.extend(["-c", config_file, "install"])
        result = self.runner.invoke(cli.cli, self.cli_args)
        self.assert_result(result, 0)

        written_config = read_yaml(config_file)

        self.assertEquals('openshift-enterprise', written_config['variant'])
        # Make sure our older version was preserved:
        # and written to disk:
        self.assertEquals('3.3', written_config['variant_version'])

        inventory = configparser.ConfigParser(allow_no_value=True)
        inventory.read(os.path.join(self.work_dir, 'hosts'))
        self.assertEquals('openshift-enterprise',
            inventory.get('OSEv3:vars', 'deployment_type'))

    # unattended with bad config file and no installed hosts (without --force)
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_bad_config(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0

        config_file = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), BAD_CONFIG % 'openshift-enterprise')

        self.cli_args.extend(["-c", config_file, "install"])
        result = self.runner.invoke(cli.cli, self.cli_args)

        self.assertEquals(1, result.exit_code)
        self.assertTrue("You must specify either an ip or hostname"
            in result.output)

    #unattended with three masters, one node, and haproxy
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_quick_ha_full_run(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS_QUICKHA, 0)
        run_playbook_mock.return_value = 0

        config_file = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), QUICKHA_CONFIG % 'openshift-enterprise')

        self.cli_args.extend(["-c", config_file, "install"])
        result = self.runner.invoke(cli.cli, self.cli_args)
        self.assert_result(result, 0)

        # Make sure we ran on the expected masters and nodes:
        hosts = run_playbook_mock.call_args[0][1]
        hosts_to_run_on = run_playbook_mock.call_args[0][2]
        self.assertEquals(6, len(hosts))
        self.assertEquals(6, len(hosts_to_run_on))

    #unattended with two masters, one node, and haproxy
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_quick_ha_only_2_masters(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS_QUICKHA, 0)
        run_playbook_mock.return_value = 0

        config_file = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), QUICKHA_2_MASTER_CONFIG % 'openshift-enterprise')

        self.cli_args.extend(["-c", config_file, "install"])
        result = self.runner.invoke(cli.cli, self.cli_args)

        # This is an invalid config:
        self.assert_result(result, 1)
        self.assertTrue("A minimum of 3 masters are required" in result.output)

    #unattended with three masters, one node, but no load balancer specified:
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_quick_ha_no_lb(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS_QUICKHA, 0)
        run_playbook_mock.return_value = 0

        config_file = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), QUICKHA_CONFIG_NO_LB % 'openshift-enterprise')

        self.cli_args.extend(["-c", config_file, "install"])
        result = self.runner.invoke(cli.cli, self.cli_args)

        # This is not a valid input:
        self.assert_result(result, 1)
        self.assertTrue('No master load balancer specified in config' in result.output)

    #unattended with three masters, one node, and one of the masters reused as load balancer:
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_quick_ha_reused_lb(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS_QUICKHA, 0)
        run_playbook_mock.return_value = 0

        config_file = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), QUICKHA_CONFIG_REUSED_LB % 'openshift-enterprise')

        self.cli_args.extend(["-c", config_file, "install"])
        result = self.runner.invoke(cli.cli, self.cli_args)

        # This is not a valid configuration:
        self.assert_result(result, 1)

    #unattended with preconfigured lb
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_quick_ha_preconfigured_lb(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS_QUICKHA, 0)
        run_playbook_mock.return_value = 0

        config_file = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), QUICKHA_CONFIG_PRECONFIGURED_LB % 'openshift-enterprise')

        self.cli_args.extend(["-c", config_file, "install"])
        result = self.runner.invoke(cli.cli, self.cli_args)
        self.assert_result(result, 0)

        # Make sure we ran on the expected masters and nodes:
        hosts = run_playbook_mock.call_args[0][1]
        hosts_to_run_on = run_playbook_mock.call_args[0][2]
        self.assertEquals(6, len(hosts))
        self.assertEquals(6, len(hosts_to_run_on))

class AttendedCliTests(OOCliFixture):

    def setUp(self):
        OOCliFixture.setUp(self)
        # Doesn't exist but keeps us from reading the local users config:
        self.config_file = os.path.join(self.work_dir, 'config.yml')
        self.cli_args.extend(["-c", self.config_file])

    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_full_run(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0

        cli_input = build_input(hosts=[
            ('10.0.0.1', True, False),
            ('10.0.0.2', False, False),
            ('10.0.0.3', False, False)],
                                      ssh_user='root',
                                      variant_num=1,
                                      confirm_facts='y',
                                      storage='10.1.0.1',)
        self.cli_args.append("install")
        result = self.runner.invoke(cli.cli, self.cli_args,
            input=cli_input)
        self.assert_result(result, 0)

        self._verify_load_facts(load_facts_mock)
        self._verify_run_playbook(run_playbook_mock, 4, 4)

        written_config = read_yaml(self.config_file)
        self._verify_config_hosts(written_config, 4)

        inventory = configparser.ConfigParser(allow_no_value=True)
        inventory.read(os.path.join(self.work_dir, 'hosts'))
        self.assert_inventory_host_var(inventory, 'nodes', '10.0.0.1',
                                 'openshift_schedulable=False')
        self.assert_inventory_host_var_unset(inventory, 'nodes', '10.0.0.2',
                                 'openshift_schedulable=True')
        self.assert_inventory_host_var_unset(inventory, 'nodes', '10.0.0.3',
                                 'openshift_schedulable=True')

    # interactive with config file and some installed some uninstalled hosts
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_scaleup_hint(self, load_facts_mock, run_playbook_mock):

        # Modify the mock facts to return a version indicating OpenShift
        # is already installed on our master, and the first node.
        mock_facts = copy.deepcopy(MOCK_FACTS)
        mock_facts['10.0.0.1']['common']['version'] = "3.0.0"
        mock_facts['10.0.0.2']['common']['version'] = "3.0.0"

        load_facts_mock.return_value = (mock_facts, 0)
        run_playbook_mock.return_value = 0

        cli_input = build_input(hosts=[
            ('10.0.0.1', True, False),
            ('10.0.0.2', False, False),
            ],
                                      add_nodes=[('10.0.0.3', False, False)],
                                      ssh_user='root',
                                      variant_num=1,
                                      confirm_facts='y',
                                      storage='10.0.0.1',)
        self.cli_args.append("install")
        result = self.runner.invoke(cli.cli,
                                    self.cli_args,
                                    input=cli_input)

        # This is testing the install workflow so we want to make sure we
        # exit with the appropriate hint.
        self.assertTrue('scaleup' in result.output)
        self.assert_result(result, 1)


    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_fresh_install_with_config(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0

        config_file = self.write_config(os.path.join(self.work_dir,
                                                     'ooinstall.conf'),
                                        SAMPLE_CONFIG % 'openshift-enterprise')
        cli_input = build_input(confirm_facts='y')
        self.cli_args.extend(["-c", config_file])
        self.cli_args.append("install")
        result = self.runner.invoke(cli.cli,
                                    self.cli_args,
                                    input=cli_input)
        self.assert_result(result, 0)

        self._verify_load_facts(load_facts_mock)
        self._verify_run_playbook(run_playbook_mock, 3, 3)

        written_config = read_yaml(config_file)
        self._verify_config_hosts(written_config, 3)

#    #interactive with config file and all installed hosts
#    @patch('ooinstall.openshift_ansible.run_main_playbook')
#    @patch('ooinstall.openshift_ansible.load_system_facts')
#    def test_get_hosts_to_run_on(self, load_facts_mock, run_playbook_mock):
#        mock_facts = copy.deepcopy(MOCK_FACTS)
#        mock_facts['10.0.0.1']['common']['version'] = "3.0.0"
#        mock_facts['10.0.0.2']['common']['version'] = "3.0.0"
#
#        cli_input = build_input(hosts=[
#            ('10.0.0.1', True, False),
#            ],
#                                      add_nodes=[('10.0.0.2', False, False)],
#                                      ssh_user='root',
#                                      variant_num=1,
#                                      schedulable_masters_ok=True,
#                                      confirm_facts='y',
#                                      storage='10.0.0.1',)
#
#        self._verify_get_hosts_to_run_on(mock_facts, load_facts_mock,
#                                         run_playbook_mock,
#                                         cli_input,
#                                         exp_hosts_len=2,
#                                         exp_hosts_to_run_on_len=2,
#                                         force=False)

    #interactive multimaster: one more node than master
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_ha_dedicated_node(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS_QUICKHA, 0)
        run_playbook_mock.return_value = 0

        cli_input = build_input(hosts=[
            ('10.0.0.1', True, False),
            ('10.0.0.2', True, False),
            ('10.0.0.3', True, False),
            ('10.0.0.4', False, False)],
                                      ssh_user='root',
                                      variant_num=1,
                                      confirm_facts='y',
                                      master_lb=('10.0.0.5', False),
                                      storage='10.1.0.1',)
        self.cli_args.append("install")
        result = self.runner.invoke(cli.cli, self.cli_args,
            input=cli_input)
        self.assert_result(result, 0)

        self._verify_load_facts(load_facts_mock)
        self._verify_run_playbook(run_playbook_mock, 6, 6)

        written_config = read_yaml(self.config_file)
        self._verify_config_hosts(written_config, 6)

        inventory = configparser.ConfigParser(allow_no_value=True)
        inventory.read(os.path.join(self.work_dir, 'hosts'))
        self.assert_inventory_host_var(inventory, 'nodes', '10.0.0.1',
                                       'openshift_schedulable=False')
        self.assert_inventory_host_var(inventory, 'nodes', '10.0.0.2',
                                       'openshift_schedulable=False')
        self.assert_inventory_host_var(inventory, 'nodes', '10.0.0.3',
                                       'openshift_schedulable=False')
        self.assert_inventory_host_var_unset(inventory, 'nodes', '10.0.0.4',
                                             'openshift_schedulable=True')

        self.assertTrue(inventory.has_section('etcd'))
        self.assertEquals(3, len(inventory.items('etcd')))

    #interactive multimaster: identical masters and nodes
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_ha_no_dedicated_nodes(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS_QUICKHA, 0)
        run_playbook_mock.return_value = 0

        cli_input = build_input(hosts=[
            ('10.0.0.1', True, False),
            ('10.0.0.2', True, False),
            ('10.0.0.3', True, False)],
                                      ssh_user='root',
                                      variant_num=1,
                                      confirm_facts='y',
                                      master_lb=('10.0.0.5', False),
                                      storage='10.1.0.1',)
        self.cli_args.append("install")
        result = self.runner.invoke(cli.cli, self.cli_args,
            input=cli_input)
        self.assert_result(result, 0)

        self._verify_load_facts(load_facts_mock)
        self._verify_run_playbook(run_playbook_mock, 5, 5)

        written_config = read_yaml(self.config_file)
        self._verify_config_hosts(written_config, 5)

        inventory = configparser.ConfigParser(allow_no_value=True)
        inventory.read(os.path.join(self.work_dir, 'hosts'))
        self.assert_inventory_host_var(inventory, 'nodes', '10.0.0.1',
                                       'openshift_schedulable=True')
        self.assert_inventory_host_var(inventory, 'nodes', '10.0.0.2',
                                       'openshift_schedulable=True')
        self.assert_inventory_host_var(inventory, 'nodes', '10.0.0.3',
                                       'openshift_schedulable=True')

    # Checks the inventory (as a ConfigParser) for the given host, host
    # variable, and expected value.
    def assert_inventory_host_var(self, inventory, section, host, variable):
        # Config parser splits on the first "=", so we end up with:
        #   'hostname key1' -> 'val1 key2=val2 key3=val3'
        #
        # Convert to something easier to test:
        for (a, b) in inventory.items(section):
            full_line = "%s=%s" % (a, b)
            tokens = full_line.split()
            if tokens[0] == host:
                self.assertTrue(variable in tokens[1:], "Unable to find %s in line: %s" % (variable, full_line))
                return
        self.fail("unable to find host %s in inventory" % host)

    def assert_inventory_host_var_unset(self, inventory, section, host, variable):
        # Config parser splits on the first "=", so we end up with:
        #   'hostname key1' -> 'val1 key2=val2 key3=val3'
        #
        # Convert to something easier to test:
        for (a, b) in inventory.items(section):
            full_line = "%s=%s" % (a, b)
            tokens = full_line.split()
            if tokens[0] == host:
                self.assertFalse(("%s=" % variable) in full_line,
                                 msg='%s host variable was set: %s' %
                                 (variable, full_line))
                return
        self.fail("unable to find host %s in inventory" % host)


    #interactive multimaster: attempting to use a master as the load balancer should fail:
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_ha_reuse_master_as_lb(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS_QUICKHA, 0)
        run_playbook_mock.return_value = 0

        cli_input = build_input(hosts=[
                                      ('10.0.0.1', True, False),
                                      ('10.0.0.2', True, False),
                                      ('10.0.0.3', False, False),
                                      ('10.0.0.4', True, False)],
                                      ssh_user='root',
                                      variant_num=1,
                                      confirm_facts='y',
                                      master_lb=(['10.0.0.2', '10.0.0.5'], False),
                                      storage='10.1.0.1')
        self.cli_args.append("install")
        result = self.runner.invoke(cli.cli, self.cli_args,
            input=cli_input)
        self.assert_result(result, 0)

    #interactive all-in-one
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_all_in_one(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0

        cli_input = build_input(hosts=[
            ('10.0.0.1', True, False)],
                                      ssh_user='root',
                                      variant_num=1,
                                      confirm_facts='y',
                                      storage='10.0.0.1')
        self.cli_args.append("install")
        result = self.runner.invoke(cli.cli, self.cli_args,
            input=cli_input)
        self.assert_result(result, 0)

        self._verify_load_facts(load_facts_mock)
        self._verify_run_playbook(run_playbook_mock, 1, 1)

        written_config = read_yaml(self.config_file)
        self._verify_config_hosts(written_config, 1)

        inventory = configparser.ConfigParser(allow_no_value=True)
        inventory.read(os.path.join(self.work_dir, 'hosts'))
        self.assert_inventory_host_var(inventory, 'nodes', '10.0.0.1',
                                       'openshift_schedulable=True')


    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_gen_inventory(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0

        cli_input = build_input(hosts=[
            ('10.0.0.1', True, False),
            ('10.0.0.2', False, False),
            ('10.0.0.3', False, False)],
                                ssh_user='root',
                                variant_num=1,
                                confirm_facts='y',
                                storage='10.1.0.1',)
        self.cli_args.append("install")
        self.cli_args.append("--gen-inventory")
        result = self.runner.invoke(cli.cli, self.cli_args,
            input=cli_input)
        self.assert_result(result, 0)

        self._verify_load_facts(load_facts_mock)

        # Make sure run playbook wasn't called:
        self.assertEquals(0, len(run_playbook_mock.mock_calls))

        written_config = read_yaml(self.config_file)
        self._verify_config_hosts(written_config, 4)

        inventory = configparser.ConfigParser(allow_no_value=True)
        inventory.read(os.path.join(self.work_dir, 'hosts'))
        self.assert_inventory_host_var(inventory, 'nodes', '10.0.0.1',
                                 'openshift_schedulable=False')
        self.assert_inventory_host_var_unset(inventory, 'nodes', '10.0.0.2',
                                 'openshift_schedulable=True')
        self.assert_inventory_host_var_unset(inventory, 'nodes', '10.0.0.3',
                                 'openshift_schedulable=True')


# TODO: test with config file, attended add node
# TODO: test with config file, attended new node already in config file
# TODO: test with config file, attended new node already in config file, plus manually added nodes
# TODO: test with config file, attended reject facts
