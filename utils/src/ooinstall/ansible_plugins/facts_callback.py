# TODO: Temporarily disabled due to importing old code into openshift-ansible
# repo. We will work on these over time.
# pylint: disable=bad-continuation,missing-docstring,no-self-use,invalid-name,no-value-for-parameter

import os
import yaml

class CallbackModule(object):

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

    def on_any(self, *args, **kwargs):
        pass

    def runner_on_failed(self, host, res, ignore_errors=False):
        pass

    def runner_on_ok(self, host, res):
        if res['invocation']['module_args'] == 'var=result':
            facts = res['var']['result']['ansible_facts']['openshift']
            hosts_yaml = {}
            hosts_yaml[host] = facts
            os.write(self.hosts_yaml, yaml.safe_dump(hosts_yaml))

    def runner_on_skipped(self, host, item=None):
        pass

    def runner_on_unreachable(self, host, res):
        pass

    def runner_on_no_hosts(self):
        pass

    def runner_on_async_poll(self, host, res):
        pass

    def runner_on_async_ok(self, host, res):
        pass

    def runner_on_async_failed(self, host, res):
        pass

    def playbook_on_start(self):
        pass

    def playbook_on_notify(self, host, handler):
        pass

    def playbook_on_no_hosts_matched(self):
        pass

    def playbook_on_no_hosts_remaining(self):
        pass

    def playbook_on_task_start(self, name, is_conditional):
        pass

    #pylint: disable=too-many-arguments
    def playbook_on_vars_prompt(self, varname, private=True, prompt=None,
        encrypt=None, confirm=False, salt_size=None, salt=None, default=None):
        pass

    def playbook_on_setup(self):
        pass

    def playbook_on_import_for_host(self, host, imported_file):
        pass

    def playbook_on_not_import_for_host(self, host, missing_file):
        pass

    def playbook_on_play_start(self, name):
        pass

    def playbook_on_stats(self, stats):
        pass
