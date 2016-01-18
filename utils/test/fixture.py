# pylint: disable=missing-docstring
import os
import yaml

import ooinstall.cli_installer as cli

from test.oo_config_tests import OOInstallFixture
from click.testing import CliRunner

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

def read_yaml(config_file_path):
    cfg_f = open(config_file_path, 'r')
    config = yaml.safe_load(cfg_f.read())
    cfg_f.close()
    return config


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
        if result.exit_code != exit_code:
            print "Unexpected result from CLI execution"
            print "Exit code: %s" % result.exit_code
            print "Exception: %s" % result.exception
            print result.exc_info
            import traceback
            traceback.print_exception(*result.exc_info)
            print "Output:\n%s" % result.output
            self.fail("Exception during CLI execution")

    def _verify_load_facts(self, load_facts_mock):
        """ Check that we ran load facts with expected inputs. """
        load_facts_args = load_facts_mock.call_args[0]
        self.assertEquals(os.path.join(self.work_dir, ".ansible/hosts"),
                          load_facts_args[0])
        self.assertEquals(os.path.join(self.work_dir,
                                       "playbooks/byo/openshift_facts.yml"),
                          load_facts_args[1])
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
        self.assertEquals(host_count, len(written_config['hosts']))
        for host in written_config['hosts']:
            self.assertTrue('hostname' in host)
            self.assertTrue('public_hostname' in host)
            if 'preconfigured' not in host:
                self.assertTrue(host['node'])
                self.assertTrue('ip' in host)
                self.assertTrue('public_ip' in host)

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
            config_file = self.write_config(
                os.path.join(self.work_dir,
                             'ooinstall.conf'), SAMPLE_CONFIG % 'openshift-enterprise')

            self.cli_args.extend(["-c", config_file, "install"])
            if force:
                self.cli_args.append("--force")
            result = self.runner.invoke(cli.cli, self.cli_args)
            written_config = read_yaml(config_file)
            self._verify_config_hosts(written_config, exp_hosts_len)

        self.assert_result(result, 0)
        self._verify_load_facts(load_facts_mock)
        self._verify_run_playbook(run_playbook_mock, exp_hosts_len, exp_hosts_to_run_on_len)

        # Make sure we ran on the expected masters and nodes:
        hosts = run_playbook_mock.call_args[0][0]
        hosts_to_run_on = run_playbook_mock.call_args[0][1]
        self.assertEquals(exp_hosts_len, len(hosts))
        self.assertEquals(exp_hosts_to_run_on_len, len(hosts_to_run_on))


#pylint: disable=too-many-arguments,too-many-branches,too-many-statements
def build_input(ssh_user=None, hosts=None, variant_num=None,
                add_nodes=None, confirm_facts=None, schedulable_masters_ok=None,
                master_lb=None):
    """
    Build an input string simulating a user entering values in an interactive
    attended install.

    This is intended to give us one place to update when the CLI prompts change.
    We should aim to keep this dependent on optional keyword arguments with
    sensible defaults to keep things from getting too fragile.
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
        for (host, is_master, is_containerized) in hosts:
            inputs.append(host)
            if is_master:
                inputs.append('y')
                num_masters += 1
            else:
                inputs.append('n')

            if is_containerized:
                inputs.append('container')
            else:
                inputs.append('rpm')

            #inputs.append('rpm')
            # We should not be prompted to add more hosts if we're currently at
            # 2 masters, this is an invalid HA configuration, so this question
            # will not be asked, and the user must enter the next host:
            if num_masters != 2:
                if i < len(hosts) - 1:
                    if num_masters >= 1:
                        inputs.append('y')  # Add more hosts
                else:
                    inputs.append('n')  # Done adding hosts
            i += 1

    # You can pass a single master_lb or a list if you intend for one to get rejected:
    if master_lb:
        if isinstance(master_lb[0], list) or isinstance(master_lb[0], tuple):
            inputs.extend(master_lb[0])
        else:
            inputs.append(master_lb[0])
        inputs.append('y' if master_lb[1] else 'n')

    # TODO: support option 2, fresh install
    if add_nodes:
        if schedulable_masters_ok:
            inputs.append('y')
        inputs.append('1')  # Add more nodes
        i = 0
        for (host, is_master, is_containerized) in add_nodes:
            inputs.append(host)
            if is_containerized:
                inputs.append('container')
            else:
                inputs.append('rpm')
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

