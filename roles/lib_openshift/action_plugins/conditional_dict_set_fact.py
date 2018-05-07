"""
Ansible action plugin to help with setting facts conditionally based on other facts.
"""

from ansible.plugins.action import ActionBase


DOCUMENTATION = '''
---
action_plugin: conditional_set_fact

short_description: This will set a fact if the value is defined

description:
    - "To avoid constant set_fact & when conditions for each var we can use this"

author:
    - Eric Wolinetz ewolinet@redhat.com
'''


EXAMPLES = '''
- name: Conditionally set fact
  conditional_set_fact:
    fact1: not_defined_variable

- name: Conditionally set fact
  conditional_set_fact:
    fact1: not_defined_variable
    fact2: defined_variable

- name: Conditionally set fact falling back on default
  conditional_set_fact:
    fact1: not_defined_var | defined_variable

'''


# pylint: disable=too-few-public-methods
class ActionModule(ActionBase):
    """Action plugin to execute deprecated var checks."""

    def set_dict_value(self, var_first_name, var_last_name, local_facts, var_list, var_dict_name, facts, changed):
        if var_first_name not in local_facts:
            if var_first_name in facts:
                local_facts[var_first_name] = facts[var_first_name]
            else:
                local_facts[var_first_name] = {}

        var_dict = local_facts

        other_vars = var_list.replace(" ", "")

        for other_var in other_vars.split('|'):
            if other_var in facts:
                for name in var_dict_name:
                    if name == var_last_name:
                        if name in var_dict:
                            if var_dict[name] != facts[other_var]:
                                var_dict[name] = facts[other_var]
                                changed = True
                                return
                        else:
                            var_dict[name] = facts[other_var]
                            changed = True
                            return

                    if name not in var_dict:
                        var_dict[name] = {}
                        changed = True

                    var_dict = var_dict[name]

    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)
        result['changed'] = False

        facts = self._task.args.get('facts', [])
        var_list = self._task.args.get('vars', [])

        local_facts = dict()
        changed = False

        for param in var_list:
            var_dict_name = param.split(".")

            var_first_name = var_dict_name[0]
            var_last_name = var_dict_name[len(var_dict_name) - 1]

            self.set_dict_value(var_first_name, var_last_name, local_facts, var_list[param], var_dict_name, facts, changed)

        if changed:
            result['changed'] = True

        result['ansible_facts'] = local_facts

        return result
