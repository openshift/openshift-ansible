# TODO: Temporarily disabled due to importing old code into openshift-ansible
# repo. We will work on these over time.
# pylint: disable=bad-continuation,missing-docstring,no-self-use,invalid-name,no-value-for-parameter

import os
import yaml
from ansible.plugins.callback import CallbackBase
from ansible.parsing.yaml.dumper import AnsibleDumper

from ansible.module_utils.six import u


# pylint: disable=super-init-not-called
class CallbackModule(CallbackBase):

    def __init__(self):
        ######################
        # This is ugly stoopid. This should be updated in the following ways:
        # 1) it should probably only be used for the
        # openshift_facts.yml playbook, so maybe there's some way to check
        # a variable that's set when that playbook is run?
        try:
            self.hosts_yaml_name = os.environ['OO_INSTALL_CALLBACK_FACTS_YAML']
        except KeyError:
            raise ValueError('The OO_INSTALL_CALLBACK_FACTS_YAML environment '
                             'variable must be set.')
        self.hosts_yaml = os.open(self.hosts_yaml_name, os.O_CREAT |
                                  os.O_WRONLY)

    def v2_on_any(self, *args, **kwargs):
        pass

    def v2_runner_on_failed(self, res, ignore_errors=False):
        pass

    # pylint: disable=protected-access
    def v2_runner_on_ok(self, res):
        abridged_result = res._result.copy()
        # Collect facts result from playbooks/byo/openshift_facts.yml
        if 'result' in abridged_result:
            facts = abridged_result['result']['ansible_facts']['openshift']
            hosts_yaml = {}
            hosts_yaml[res._host.get_name()] = facts
            to_dump = u(yaml.dump(hosts_yaml,
                                  allow_unicode=True,
                                  default_flow_style=False,
                                  Dumper=AnsibleDumper))
            os.write(self.hosts_yaml, to_dump)

    def v2_runner_on_skipped(self, res):
        pass

    def v2_runner_on_unreachable(self, res):
        pass

    def v2_runner_on_no_hosts(self, task):
        pass

    def v2_runner_on_async_poll(self, res):
        pass

    def v2_runner_on_async_ok(self, res):
        pass

    def v2_runner_on_async_failed(self, res):
        pass

    def v2_playbook_on_start(self, playbook):
        pass

    def v2_playbook_on_notify(self, res, handler):
        pass

    def v2_playbook_on_no_hosts_matched(self):
        pass

    def v2_playbook_on_no_hosts_remaining(self):
        pass

    def v2_playbook_on_task_start(self, name, is_conditional):
        pass

    # pylint: disable=too-many-arguments
    def v2_playbook_on_vars_prompt(self, varname, private=True, prompt=None,
                                   encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        pass

    def v2_playbook_on_setup(self):
        pass

    def v2_playbook_on_import_for_host(self, res, imported_file):
        pass

    def v2_playbook_on_not_import_for_host(self, res, missing_file):
        pass

    def v2_playbook_on_play_start(self, play):
        pass

    def v2_playbook_on_stats(self, stats):
        pass
