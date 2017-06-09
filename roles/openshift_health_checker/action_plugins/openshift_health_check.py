"""
Ansible action plugin to execute health checks in OpenShift clusters.
"""
# pylint: disable=wrong-import-position,missing-docstring,invalid-name
import sys
import os
from collections import defaultdict

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

from ansible.plugins.action import ActionBase

# Augment sys.path so that we can import checks from a directory relative to
# this callback plugin.
sys.path.insert(1, os.path.dirname(os.path.dirname(__file__)))

from openshift_checks import OpenShiftCheck, OpenShiftCheckException, load_checks  # noqa: E402


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)
        task_vars = task_vars or {}

        # vars are not supportably available in the callback plugin,
        # so record any it will need in the result.
        result['playbook_context'] = task_vars.get('r_openshift_health_checker_playbook_context')

        if "openshift" not in task_vars:
            result["failed"] = True
            result["msg"] = "'openshift' is undefined, did 'openshift_facts' run?"
            return result

        try:
            known_checks = self.load_known_checks()
            args = self._task.args
            resolved_checks = resolve_checks(args.get("checks", []), known_checks.values())
        except OpenShiftCheckException as e:
            result["failed"] = True
            result["msg"] = str(e)
            return result

        result["checks"] = check_results = {}

        user_disabled_checks = [
            check.strip()
            for check in task_vars.get("openshift_disable_check", "").split(",")
        ]

        for check_name in resolved_checks:
            display.banner("CHECK [{} : {}]".format(check_name, task_vars["ansible_host"]))
            check = known_checks[check_name]

            if not check.is_active(task_vars):
                r = dict(skipped=True, skipped_reason="Not active for this host")
            elif check_name in user_disabled_checks:
                r = dict(skipped=True, skipped_reason="Disabled by user request")
            else:
                try:
                    r = check.run(tmp, task_vars)
                except OpenShiftCheckException as e:
                    r = dict(
                        failed=True,
                        msg=str(e),
                    )

            check_results[check_name] = r

            if r.get("failed", False):
                result["failed"] = True
                result["msg"] = "One or more checks failed"

        result["changed"] = any(r.get("changed", False) for r in check_results.values())
        return result

    def load_known_checks(self):
        load_checks()

        known_checks = {}
        for cls in OpenShiftCheck.subclasses():
            check_name = cls.name
            if check_name in known_checks:
                other_cls = known_checks[check_name].__class__
                raise OpenShiftCheckException(
                    "non-unique check name '{}' in: '{}.{}' and '{}.{}'".format(
                        check_name,
                        cls.__module__, cls.__name__,
                        other_cls.__module__, other_cls.__name__))
            known_checks[check_name] = cls(execute_module=self._execute_module)
        return known_checks


def resolve_checks(names, all_checks):
    """Returns a set of resolved check names.

    Resolving a check name expands tag references (e.g., "@tag") to all the
    checks that contain the given tag. OpenShiftCheckException is raised if
    names contains an unknown check or tag name.

    names should be a sequence of strings.

    all_checks should be a sequence of check classes/instances.
    """
    known_check_names = set(check.name for check in all_checks)
    known_tag_names = set(name for check in all_checks for name in check.tags)

    check_names = set(name for name in names if not name.startswith('@'))
    tag_names = set(name[1:] for name in names if name.startswith('@'))

    unknown_check_names = check_names - known_check_names
    unknown_tag_names = tag_names - known_tag_names

    if unknown_check_names or unknown_tag_names:
        msg = []
        if unknown_check_names:
            msg.append('Unknown check names: {}.'.format(', '.join(sorted(unknown_check_names))))
        if unknown_tag_names:
            msg.append('Unknown tag names: {}.'.format(', '.join(sorted(unknown_tag_names))))
        msg.append('Make sure there is no typo in the playbook and no files are missing.')
        raise OpenShiftCheckException('\n'.join(msg))

    tag_to_checks = defaultdict(set)
    for check in all_checks:
        for tag in check.tags:
            tag_to_checks[tag].add(check.name)

    resolved = check_names.copy()
    for tag in tag_names:
        resolved.update(tag_to_checks[tag])

    return resolved
