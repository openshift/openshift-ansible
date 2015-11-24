# TODO: Temporarily disabled due to importing old code into openshift-ansible
# repo. We will work on these over time.
# pylint: disable=bad-continuation,missing-docstring,no-self-use,invalid-name

import copy
import os
import ConfigParser
import yaml

import ooinstall.cli_installer as cli

from click.testing import CliRunner
from test.oo_config_tests import OOInstallFixture
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
            'hostname': 'proxy-private.example.com',
            'public_hostname': 'proxy.example.com'
        }
    },
}

# Substitute in a product name before use:
SAMPLE_CONFIG = """
variant: %s
ansible_ssh_user: root
hosts:
  - connect_to: 10.0.0.1
    ip: 10.0.0.1
    hostname: master-private.example.com
    public_ip: 24.222.0.1
    public_hostname: master.example.com
    master: true
    node: true
  - connect_to: 10.0.0.2
    ip: 10.0.0.2
    hostname: node1-private.example.com
    public_ip: 24.222.0.2
    public_hostname: node1.example.com
    node: true
  - connect_to: 10.0.0.3
    ip: 10.0.0.3
    hostname: node2-private.example.com
    public_ip: 24.222.0.3
    public_hostname: node2.example.com
    node: true
"""

BAD_CONFIG = """
variant: %s
ansible_ssh_user: root
hosts:
  - connect_to: 10.0.0.1
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
  - connect_to: 10.0.0.3
    ip: 10.0.0.3
    hostname: node2-private.example.com
    public_ip: 24.222.0.3
    public_hostname: node2.example.com
    node: true
"""

QUICKHA_CONFIG = """
variant: %s
ansible_ssh_user: root
hosts:
  - connect_to: 10.0.0.1
    ip: 10.0.0.1
    hostname: master-private.example.com
    public_ip: 24.222.0.1
    public_hostname: master.example.com
    master: true
    node: true
  - connect_to: 10.0.0.2
    ip: 10.0.0.2
    hostname: node1-private.example.com
    public_ip: 24.222.0.2
    public_hostname: node1.example.com
    master: true
    node: true
  - connect_to: 10.0.0.3
    ip: 10.0.0.3
    hostname: node2-private.example.com
    public_ip: 24.222.0.3
    public_hostname: node2.example.com
    node: true
  - connect_to: 10.0.0.4
    ip: 10.0.0.4
    hostname: proxy-private.example.com
    public_ip: 24.222.0.4
    public_hostname: proxy.example.com
    master_lb: true
"""

class OOCliFixture(OOInstallFixture):

    def setUp(self):
        OOInstallFixture.setUp(self)
        self.runner = CliRunner()

        # Add any arguments you would like to test here, the defaults ensure
        # we only do unattended invocations here, and using temporary files/dirs.
        self.cli_args = ["-a", self.work_dir]

    def run_cli(self):
        return self.runner.invoke(cli.cli, self.cli_args)

    def assert_result(self, result, exit_code):
        if result.exception is not None or result.exit_code != exit_code:
            print "Unexpected result from CLI execution"
            print "Exit code: %s" % result.exit_code
            print "Exception: %s" % result.exception
            print result.exc_info
            import traceback
            traceback.print_exception(*result.exc_info)
            print "Output:\n%s" % result.output
            self.fail("Exception during CLI execution")

    def _read_yaml(self, config_file_path):
        f = open(config_file_path, 'r')
        config = yaml.safe_load(f.read())
        f.close()
        return config

    def _verify_load_facts(self, load_facts_mock):
        """ Check that we ran load facts with expected inputs. """
        load_facts_args = load_facts_mock.call_args[0]
        self.assertEquals(os.path.join(self.work_dir, ".ansible/hosts"),
            load_facts_args[0])
        self.assertEquals(os.path.join(self.work_dir,
            "playbooks/byo/openshift_facts.yml"), load_facts_args[1])
        env_vars = load_facts_args[2]
        self.assertEquals(os.path.join(self.work_dir,
            '.ansible/callback_facts.yaml'),
            env_vars['OO_INSTALL_CALLBACK_FACTS_YAML'])
        self.assertEqual('/tmp/ansible.log', env_vars['ANSIBLE_LOG_PATH'])

    def _verify_run_playbook(self, run_playbook_mock, exp_hosts_len, exp_hosts_to_run_on_len):
        """ Check that we ran playbook with expected inputs. """
        hosts = run_playbook_mock.call_args[0][0]
        hosts_to_run_on = run_playbook_mock.call_args[0][1]
        self.assertEquals(exp_hosts_len, len(hosts))
        self.assertEquals(exp_hosts_to_run_on_len, len(hosts_to_run_on))

    def _verify_config_hosts(self, written_config, host_count):
        print written_config['hosts']
        self.assertEquals(host_count, len(written_config['hosts']))
        for h in written_config['hosts']:
            self.assertTrue('hostname' in h)
            self.assertTrue('public_hostname' in h)
            if 'preconfigured' not in h:
                self.assertTrue(h['node'])
                self.assertTrue('ip' in h)
                self.assertTrue('public_ip' in h)

    #pylint: disable=too-many-arguments
    def _verify_get_hosts_to_run_on(self, mock_facts, load_facts_mock,
                                    run_playbook_mock, cli_input,
                                    exp_hosts_len=None, exp_hosts_to_run_on_len=None,
                                    force=None):
        """
        Tests cli_installer.py:get_hosts_to_run_on.  That method has quite a
        few subtle branches in the logic.  The goal with this method is simply
        to handle all the messy stuff here and allow the main test cases to be
        easily read.  The basic idea is to modify mock_facts to return a
        version indicating OpenShift is already installed on particular hosts.
        """
        load_facts_mock.return_value = (mock_facts, 0)
        run_playbook_mock.return_value = 0

        if cli_input:
            self.cli_args.append("install")
            result = self.runner.invoke(cli.cli,
                                        self.cli_args,
                                        input=cli_input)
        else:
            config_file = self.write_config(os.path.join(self.work_dir,
                'ooinstall.conf'), SAMPLE_CONFIG % 'openshift-enterprise')

            self.cli_args.extend(["-c", config_file, "install"])
            if force:
                self.cli_args.append("--force")
            result = self.runner.invoke(cli.cli, self.cli_args)
            written_config = self._read_yaml(config_file)
            self._verify_config_hosts(written_config, exp_hosts_len)

        self.assert_result(result, 0)
        self._verify_load_facts(load_facts_mock)
        self._verify_run_playbook(run_playbook_mock, exp_hosts_len, exp_hosts_to_run_on_len)

        # Make sure we ran on the expected masters and nodes:
        hosts = run_playbook_mock.call_args[0][0]
        hosts_to_run_on = run_playbook_mock.call_args[0][1]
        self.assertEquals(exp_hosts_len, len(hosts))
        self.assertEquals(exp_hosts_to_run_on_len, len(hosts_to_run_on))

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
            print "Exit code: %s" % result.exit_code
            self.fail("Unexpected CLI return")

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
        self.assertEquals(os.path.join(self.work_dir, ".ansible/hosts"),
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
        hosts = run_playbook_mock.call_args[0][0]
        hosts_to_run_on = run_playbook_mock.call_args[0][1]
        self.assertEquals(3, len(hosts))
        self.assertEquals(3, len(hosts_to_run_on))

    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_inventory_write(self, load_facts_mock, run_playbook_mock):

        # Add an ssh user so we can verify it makes it to the inventory file:
        merged_config = "%s\n%s" % (SAMPLE_CONFIG % 'openshift-enterprise',
            "ansible_ssh_user: bob")
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0

        config_file = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), merged_config)

        self.cli_args.extend(["-c", config_file, "install"])
        result = self.runner.invoke(cli.cli, self.cli_args)
        self.assert_result(result, 0)

        # Check the inventory file looks as we would expect:
        inventory = ConfigParser.ConfigParser(allow_no_value=True)
        inventory.read(os.path.join(self.work_dir, '.ansible/hosts'))
        self.assertEquals('bob',
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

        written_config = self._read_yaml(config_file)

        self.assertEquals('openshift-enterprise', written_config['variant'])
        # We didn't specify a version so the latest should have been assumed,
        # and written to disk:
        self.assertEquals('3.1', written_config['variant_version'])

        # Make sure the correct value was passed to ansible:
        inventory = ConfigParser.ConfigParser(allow_no_value=True)
        inventory.read(os.path.join(self.work_dir, '.ansible/hosts'))
        self.assertEquals('openshift-enterprise',
            inventory.get('OSEv3:vars', 'deployment_type'))

    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_variant_version_preserved(self, load_facts_mock,
        run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0

        config = SAMPLE_CONFIG % 'openshift-enterprise'
        config = '%s\n%s' % (config, 'variant_version: 3.0')
        config_file = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), config)

        self.cli_args.extend(["-c", config_file, "install"])
        result = self.runner.invoke(cli.cli, self.cli_args)
        self.assert_result(result, 0)

        written_config = self._read_yaml(config_file)

        self.assertEquals('openshift-enterprise', written_config['variant'])
        # Make sure our older version was preserved:
        # and written to disk:
        self.assertEquals('3.0', written_config['variant_version'])

        inventory = ConfigParser.ConfigParser(allow_no_value=True)
        inventory.read(os.path.join(self.work_dir, '.ansible/hosts'))
        self.assertEquals('enterprise',
            inventory.get('OSEv3:vars', 'deployment_type'))

    @patch('ooinstall.openshift_ansible.run_ansible')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_no_ansible_config_specified(self, load_facts_mock, run_ansible_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_ansible_mock.return_value = 0

        config = SAMPLE_CONFIG % 'openshift-enterprise'

        self._ansible_config_test(load_facts_mock, run_ansible_mock,
            config, None, None)

    @patch('ooinstall.openshift_ansible.run_ansible')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_ansible_config_specified_cli(self, load_facts_mock, run_ansible_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_ansible_mock.return_value = 0

        config = SAMPLE_CONFIG % 'openshift-enterprise'
        ansible_config = os.path.join(self.work_dir, 'ansible.cfg')

        self._ansible_config_test(load_facts_mock, run_ansible_mock,
            config, ansible_config, ansible_config)

    @patch('ooinstall.openshift_ansible.run_ansible')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_ansible_config_specified_in_installer_config(self,
        load_facts_mock, run_ansible_mock):

        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_ansible_mock.return_value = 0

        ansible_config = os.path.join(self.work_dir, 'ansible.cfg')
        config = SAMPLE_CONFIG % 'openshift-enterprise'
        config = "%s\nansible_config: %s" % (config, ansible_config)
        self._ansible_config_test(load_facts_mock, run_ansible_mock,
            config, None, ansible_config)

    #pylint: disable=too-many-arguments
    # This method allows for drastically simpler tests to write, and the args
    # are all useful.
    def _ansible_config_test(self, load_facts_mock, run_ansible_mock,
        installer_config, ansible_config_cli=None, expected_result=None):
        """
        Utility method for testing the ways you can specify the ansible config.
        """

        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_ansible_mock.return_value = 0

        config_file = self.write_config(os.path.join(self.work_dir,
            'ooinstall.conf'), installer_config)

        self.cli_args.extend(["-c", config_file])
        if ansible_config_cli:
            self.cli_args.extend(["--ansible-config", ansible_config_cli])
        self.cli_args.append("install")
        result = self.runner.invoke(cli.cli, self.cli_args)
        self.assert_result(result, 0)

        # Test the env vars for facts playbook:
        facts_env_vars = load_facts_mock.call_args[0][2]
        if expected_result:
            self.assertEquals(expected_result, facts_env_vars['ANSIBLE_CONFIG'])
        else:
            # If user running test has rpm installed, this might be set to default:
            self.assertTrue('ANSIBLE_CONFIG' not in facts_env_vars or
                facts_env_vars['ANSIBLE_CONFIG'] == cli.DEFAULT_ANSIBLE_CONFIG)

        # Test the env vars for main playbook:
        env_vars = run_ansible_mock.call_args[0][2]
        if expected_result:
            self.assertEquals(expected_result, env_vars['ANSIBLE_CONFIG'])
        else:
            # If user running test has rpm installed, this might be set to default:
            self.assertTrue('ANSIBLE_CONFIG' not in env_vars or
                env_vars['ANSIBLE_CONFIG'] == cli.DEFAULT_ANSIBLE_CONFIG)

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

        assert result.exit_code == 1
        assert result.output == "You must specify either and 'ip' or 'hostname' to connect to.\n"

    #unattended with two masters, one node, and haproxy
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

        load_facts_args = load_facts_mock.call_args[0]
        self.assertEquals(os.path.join(self.work_dir, ".ansible/hosts"),
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
        hosts = run_playbook_mock.call_args[0][0]
        hosts_to_run_on = run_playbook_mock.call_args[0][1]
        self.assertEquals(4, len(hosts))
        self.assertEquals(4, len(hosts_to_run_on))

class AttendedCliTests(OOCliFixture):

    def setUp(self):
        OOCliFixture.setUp(self)
        # Doesn't exist but keeps us from reading the local users config:
        self.config_file = os.path.join(self.work_dir, 'config.yml')
        self.cli_args.extend(["-c", self.config_file])

    #pylint: disable=too-many-arguments,too-many-branches
    def _build_input(self, ssh_user=None, hosts=None, variant_num=None,
        add_nodes=None, confirm_facts=None, scheduleable_masters_ok=None,
        master_lb=None):
        """
        Builds a CLI input string with newline characters to simulate
        the full run.
        This gives us only one place to update when the input prompts change.
        """

        inputs = [
            'y',  # let's proceed
        ]
        if ssh_user:
            inputs.append(ssh_user)

        if variant_num:
            inputs.append(str(variant_num))  # Choose variant + version

        num_masters = 0
        if hosts:
            i = 0
            min_masters_for_ha = 3
            for (host, is_master) in hosts:
                inputs.append(host)
                if is_master:
                    inputs.append('y')
                    num_masters += 1
                else:
                    inputs.append('n')
                #inputs.append('rpm')
                if i < len(hosts) - 1:
                    if num_masters <= 1 or num_masters >= min_masters_for_ha:
                        inputs.append('y')  # Add more hosts
                else:
                    inputs.append('n')  # Done adding hosts
                i += 1

        if master_lb:
            inputs.append(master_lb[0])
            inputs.append('y' if master_lb[1] else 'n')

        # TODO: support option 2, fresh install
        if add_nodes:
            if scheduleable_masters_ok:
                inputs.append('y')
            inputs.append('1')  # Add more nodes
            i = 0
            for (host, is_master) in add_nodes:
                inputs.append(host)
                #inputs.append('rpm')
                if i < len(add_nodes) - 1:
                    inputs.append('y')  # Add more hosts
                else:
                    inputs.append('n')  # Done adding hosts
                i += 1

        if add_nodes is None:
            total_hosts = hosts
        else:
            total_hosts = hosts + add_nodes
        if total_hosts is not None and num_masters == len(total_hosts):
            inputs.append('y')

        inputs.extend([
            confirm_facts,
            'y',  # lets do this
        ])

        return '\n'.join(inputs)

    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_full_run(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0

        cli_input = self._build_input(hosts=[
            ('10.0.0.1', True),
            ('10.0.0.2', False),
            ('10.0.0.3', False)],
                                      ssh_user='root',
                                      variant_num=1,
                                      confirm_facts='y')
        self.cli_args.append("install")
        result = self.runner.invoke(cli.cli, self.cli_args,
            input=cli_input)
        self.assert_result(result, 0)

        self._verify_load_facts(load_facts_mock)
        self._verify_run_playbook(run_playbook_mock, 3, 3)

        written_config = self._read_yaml(self.config_file)
        self._verify_config_hosts(written_config, 3)

        inventory = ConfigParser.ConfigParser(allow_no_value=True)
        inventory.read(os.path.join(self.work_dir, '.ansible/hosts'))
        self.assertEquals('False',
            inventory.get('nodes', '10.0.0.1  openshift_scheduleable'))
        self.assertEquals(None,
            inventory.get('nodes', '10.0.0.2'))
        self.assertEquals(None,
            inventory.get('nodes', '10.0.0.3'))

    # interactive with config file and some installed some uninstalled hosts
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_add_nodes(self, load_facts_mock, run_playbook_mock):

        # Modify the mock facts to return a version indicating OpenShift
        # is already installed on our master, and the first node.
        mock_facts = copy.deepcopy(MOCK_FACTS)
        mock_facts['10.0.0.1']['common']['version'] = "3.0.0"
        mock_facts['10.0.0.2']['common']['version'] = "3.0.0"

        load_facts_mock.return_value = (mock_facts, 0)
        run_playbook_mock.return_value = 0

        cli_input = self._build_input(hosts=[
            ('10.0.0.1', True),
            ('10.0.0.2', False),
            ],
                                      add_nodes=[('10.0.0.3', False)],
                                      ssh_user='root',
                                      variant_num=1,
                                      confirm_facts='y')
        self.cli_args.append("install")
        result = self.runner.invoke(cli.cli,
                                    self.cli_args,
                                    input=cli_input)
        print result
        self.assert_result(result, 0)

        self._verify_load_facts(load_facts_mock)
        self._verify_run_playbook(run_playbook_mock, 3, 2)

        written_config = self._read_yaml(self.config_file)
        self._verify_config_hosts(written_config, 3)

    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_fresh_install_with_config(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0

        config_file = self.write_config(os.path.join(self.work_dir,
                                                     'ooinstall.conf'),
                                        SAMPLE_CONFIG % 'openshift-enterprise')
        cli_input = self._build_input(confirm_facts='y')
        self.cli_args.extend(["-c", config_file])
        self.cli_args.append("install")
        result = self.runner.invoke(cli.cli,
                                    self.cli_args,
                                    input=cli_input)
        self.assert_result(result, 0)

        self._verify_load_facts(load_facts_mock)
        self._verify_run_playbook(run_playbook_mock, 3, 3)

        written_config = self._read_yaml(config_file)
        self._verify_config_hosts(written_config, 3)

    #interactive with config file and all installed hosts
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_get_hosts_to_run_on(self, load_facts_mock, run_playbook_mock):
        mock_facts = copy.deepcopy(MOCK_FACTS)
        mock_facts['10.0.0.1']['common']['version'] = "3.0.0"
        mock_facts['10.0.0.2']['common']['version'] = "3.0.0"

        cli_input = self._build_input(hosts=[
            ('10.0.0.1', True),
            ],
                                      add_nodes=[('10.0.0.2', False)],
                                      ssh_user='root',
                                      variant_num=1,
                                      scheduleable_masters_ok=True,
                                      confirm_facts='y')

        self._verify_get_hosts_to_run_on(mock_facts, load_facts_mock,
                                         run_playbook_mock,
                                         cli_input,
                                         exp_hosts_len=2,
                                         exp_hosts_to_run_on_len=2,
                                         force=False)

    #interactive multimaster: one more node than master
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_quick_ha1(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS_QUICKHA, 0)
        run_playbook_mock.return_value = 0

        cli_input = self._build_input(hosts=[
            ('10.0.0.1', True),
            ('10.0.0.2', True),
            ('10.0.0.3', False),
            ('10.0.0.4', True)],
                                      ssh_user='root',
                                      variant_num=1,
                                      confirm_facts='y',
                                      master_lb=('10.0.0.5', False))
        self.cli_args.append("install")
        result = self.runner.invoke(cli.cli, self.cli_args,
            input=cli_input)
        self.assert_result(result, 0)

        self._verify_load_facts(load_facts_mock)
        self._verify_run_playbook(run_playbook_mock, 5, 5)

        written_config = self._read_yaml(self.config_file)
        self._verify_config_hosts(written_config, 5)

        inventory = ConfigParser.ConfigParser(allow_no_value=True)
        inventory.read(os.path.join(self.work_dir, '.ansible/hosts'))
        self.assertEquals('False',
            inventory.get('nodes', '10.0.0.1  openshift_scheduleable'))
        self.assertEquals('False',
            inventory.get('nodes', '10.0.0.2  openshift_scheduleable'))
        self.assertEquals(None,
            inventory.get('nodes', '10.0.0.3'))
        self.assertEquals('False',
            inventory.get('nodes', '10.0.0.4  openshift_scheduleable'))

        return

    #interactive multimaster: equal number masters and nodes
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_quick_ha2(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS_QUICKHA, 0)
        run_playbook_mock.return_value = 0

        cli_input = self._build_input(hosts=[
            ('10.0.0.1', True),
            ('10.0.0.2', True),
            ('10.0.0.3', True)],
                                      ssh_user='root',
                                      variant_num=1,
                                      confirm_facts='y',
                                      master_lb=('10.0.0.5', False))
        self.cli_args.append("install")
        result = self.runner.invoke(cli.cli, self.cli_args,
            input=cli_input)
        self.assert_result(result, 0)

        self._verify_load_facts(load_facts_mock)
        self._verify_run_playbook(run_playbook_mock, 4, 4)

        written_config = self._read_yaml(self.config_file)
        self._verify_config_hosts(written_config, 4)

        inventory = ConfigParser.ConfigParser(allow_no_value=True)
        inventory.read(os.path.join(self.work_dir, '.ansible/hosts'))
        self.assertEquals(None,
            inventory.get('nodes', '10.0.0.1'))
        self.assertEquals(None,
            inventory.get('nodes', '10.0.0.2'))
        self.assertEquals(None,
            inventory.get('nodes', '10.0.0.3'))

        return

    #interactive all-in-one
    @patch('ooinstall.openshift_ansible.run_main_playbook')
    @patch('ooinstall.openshift_ansible.load_system_facts')
    def test_all_in_one(self, load_facts_mock, run_playbook_mock):
        load_facts_mock.return_value = (MOCK_FACTS, 0)
        run_playbook_mock.return_value = 0

        cli_input = self._build_input(hosts=[
            ('10.0.0.1', True)],
                                      ssh_user='root',
                                      variant_num=1,
                                      confirm_facts='y')
        self.cli_args.append("install")
        result = self.runner.invoke(cli.cli, self.cli_args,
            input=cli_input)
        self.assert_result(result, 0)

        self._verify_load_facts(load_facts_mock)
        self._verify_run_playbook(run_playbook_mock, 1, 1)

        written_config = self._read_yaml(self.config_file)
        self._verify_config_hosts(written_config, 1)

        inventory = ConfigParser.ConfigParser(allow_no_value=True)
        inventory.read(os.path.join(self.work_dir, '.ansible/hosts'))
        self.assertEquals(None,
            inventory.get('nodes', '10.0.0.1'))

        return

# TODO: test with config file, attended add node
# TODO: test with config file, attended new node already in config file
# TODO: test with config file, attended new node already in config file, plus manually added nodes
# TODO: test with config file, attended reject facts
