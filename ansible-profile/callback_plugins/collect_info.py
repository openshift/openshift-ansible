# Copyright 2016 Red Hat, Inc. and/or its affiliates
# and other contributors as indicated by the @author tags.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''
A plugin to collect openshift-ansible info
'''

from yaml import yaml
from json import json


class DictDiffer(object):
    """
    Calculate the difference between two dictionaries
    """
    def __init__(self, current_dict, past_dict):
        self.current_dict, self.past_dict = current_dict, past_dict
        self.set_current, self.set_past = set(current_dict.keys()), set(past_dict.keys())
        self.intersect = self.set_current.intersection(self.set_past)

    def added(self):
        "Return a list of added items"
        return self.set_current - self.intersect

    def removed(self):
        "Return a list of removed items"
        return self.set_past - self.intersect

    def changed(self):
        "Return a list of changed items (top-level)"
        return set(o for o in self.intersect if self.past_dict[o] != self.current_dict[o])

    def recursive_changed(self, chain=None):
        "Return a list of changed items (includes new items and recurses over the dicts)"
        result = []
        if not chain:
            chain = []

        changed = list(self.changed()) + list(self.added())
        for change in changed:
            old_value = self.past_dict.get(change)
            new_value = self.current_dict.get(change)
            if isinstance(old_value, dict) or isinstance(new_value, dict):
                diff = DictDiffer(new_value or {}, old_value or {})
                recursive_result = diff.recursive_changed(chain + [change])
                result += recursive_result
            else:
                result.append({
                    'chain': chain,
                    'leaf': change,
                    'old': old_value,
                    'new': new_value})
        return result


class CallbackModule(object):
    """
    A plugin to collect openshift-ansible info
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'collect_info'

    # only needed if you ship it and don't want to enable by default
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):
        # TODO: Read ansible log file setting
        self.log_file_path = '/tmp/ansible.log'
        self.log_file = open(self.log_file_path, "w+")

        # Store vars for fact changes
        self.playvars = {}
        self.inventory = None
        self.variable_manager = None

    def __dump(self, object):
        # Dump object as json
        dict_object = object.__dict__ if '__dict__' in object else object
        object_json = json.dumps(dict_object, skipkeys=True, ensure_ascii=False)
        object_yaml = yaml.safe_load(object_json)
        return yaml.safe_dump(object_yaml, default_flow_style=False, allow_unicode=True, explicit_start=True)

    def __write_task_details(self, result):
        task_name = result.task_name
        task_path = result._task.get_path()
        task_result = result._result
        task_vars = result._task.vars
        host = result._host
        task_status = "FAILED" if result.is_failed() else "ok"

        self.log_file.write('TASK {}\n'.format(task_name))
        self.log_file.write('{}\n'.format(task_path))
        self.log_file.write('{} -> {}\n'.format(host, task_status))
        if task_vars:
            vars_yaml_formatted = self.__dump(task_result)
            self.log_file.write('vars:\n{}\n'.format(vars_yaml_formatted))
        if task_result:
            results_yaml_formatted = self.__dump(task_result)
            self.log_file.write('{}\n'.format(results_yaml_formatted))

        if not result.is_failed():
            self.__log_hostvars_changes()
        self.log_file.write('--------')
        self.log_file.write('\n')
        self.log_file.flush()

    def __convert_to_dict(self, hostvars):
        """
        Convert Ansible's HostVar object in a proper dict
        so that it can be properly compared
        """
        result = {}
        if not hasattr(hostvars, 'items'):
            return result
        for key, value in hostvars.items():
            result[key] = value
        return result

    def __pretty_print_change(self, changes):
        """
        This method would return a summary of hostvar changes
        """
        result = []
        for item in changes:
            old_value = item['old']
            new_value = item['new']

            key = '.'.join(item['chain'] + [item['leaf']])

            if old_value and new_value:
                result.append("  {0}:\n    -'{1}'\n    +'{2}'".format(
                    key,
                    self.__dump(dict(item['old'])),
                    self.__dump(dict(item['new']))
                ))
            elif not old_value:
                result.append("  {0}:\n    +'{1}'".format(
                    key,
                    self.__dump(dict(item['new']))
                ))
        return '\n'.join(result)

    def __log_hostvars_changes(self):
        # Store facts diff
        old_vars = self.playvars or {}
        new_vars = self.__convert_to_dict(self.variable_manager.get_vars().get('hostvars', None))

        if old_vars and new_vars and old_vars != new_vars:
            diff = DictDiffer(new_vars, old_vars)
            changed = diff.recursive_changed()
            if changed:
                self.log_file.write('---\n')
                self.log_file.write('facts changes:\n{}\n'.format(self.__pretty_print_change(changed)))
                self.log_file.flush()

        self.playvars = new_vars

    def v2_playbook_on_start(self, playbook):
        self.log_file.write('Started playbook {}\n\n'.format(playbook._file_name))

    def v2_playbook_on_play_start(self, play):
        self.variable_manager = play.get_variable_manager()

    def runner_on_ok(self, result):
        self.__write_task_details(result)

    def runner_on_failed(self, result):
        self.__write_task_details(result)

    def playbook_on_stats(self, stats):
        self.log_file.write('Playbook finished\n')
        self.log_file.close()
        print("Deploy info is stored in {}".format(self.log_file_path))
