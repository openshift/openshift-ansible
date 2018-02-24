"""
This is a callback plugin to log changes in hostvars
"""
from __future__ import (absolute_import, division, print_function)

from ansible.plugins.callback import CallbackBase

# Maximum length of new value (-3 for dots)
MAX_LENGTH = 147


def _convert_to_dict(hostvars):
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


def _ellipsize(value):
    """
    Shorten long string
    """
    # TODO: ellipsize in the middle of the string?
    result_string = value
    if value and len(str(value)) > MAX_LENGTH:
        result_string = str(value)[:MAX_LENGTH] + '...'
    return result_string


def pretty_print_change(changes):
    """
    This method would return a summary of hostvar changes
    """
    result = []
    for item in changes:
        old_value = _ellipsize(item['old'])
        new_value = _ellipsize(item['new'])

        key = '.'.join(item['chain'] + [item['leaf']])

        if old_value and new_value:
            result.append("  {0}:\n    -'{1}'\n    +'{2}'".format(
                key,
                _ellipsize(item['old']),
                _ellipsize(item['new'])
            ))
        elif not old_value:
            result.append("  {0}:\n    +'{1}'".format(
                key, _ellipsize(item['new'])
            ))
    return '\n'.join(result)


class CallbackModule(CallbackBase):
    """
    This callback module would log changes in hostvars
    """
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'hostvars_logger'
    CALLBACK_NEEDS_WHITELIST = True

    def __init__(self):

        super(CallbackModule, self).__init__()

        self.playvars = {}
        self.inventory = None
        self.variable_manager = None

    def v2_playbook_on_play_start(self, play):
        self.variable_manager = play.get_variable_manager()

    def v2_runner_on_ok(self, _):
        old_vars = self.playvars or {}
        new_vars = _convert_to_dict(self.variable_manager.get_vars().get('hostvars', None))

        if old_vars and new_vars and old_vars != new_vars:
            diff = DictDiffer(new_vars, old_vars)
            changed = diff.recursive_changed()
            if changed:
                print("hostvars_logger:\n{}".format(pretty_print_change(changed)))

        self.playvars = new_vars


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
