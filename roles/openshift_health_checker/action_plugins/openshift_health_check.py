"""
Ansible action plugin to execute health checks in OpenShift clusters.
"""
# pylint: disable=wrong-import-position,missing-docstring,invalid-name
import sys
import os

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()

from ansible.plugins.action import ActionBase

# Augment sys.path so that we can import checks from a directory relative to
# this callback plugin.
sys.path.insert(1, os.path.dirname(os.path.dirname(__file__)))

from openshift_checks import OpenShiftCheck, OpenShiftCheckException  # noqa: E402


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)

        if task_vars is None:
            task_vars = {}

        if "openshift" not in task_vars:
            result["failed"] = True
            result["msg"] = "'openshift' is undefined, did 'openshift_facts' run?"
            return result

        try:
            known_checks = self.load_known_checks()
        except OpenShiftCheckException as e:
            result["failed"] = True
            result["msg"] = str(e)
            return result

        args = self._task.args
        requested_checks = resolve_checks(args.get("checks", []), known_checks.values())

        unknown_checks = requested_checks - set(known_checks)
        if unknown_checks:
            result["failed"] = True
            result["msg"] = (
                "One or more checks are unknown: {}. "
                "Make sure there is no typo in the playbook and no files are missing."
            ).format(", ".join(unknown_checks))
            return result

        result["checks"] = check_results = {}

        for check_name in requested_checks & set(known_checks):
            display.banner("CHECK [{} : {}]".format(check_name, task_vars["ansible_host"]))
            check = known_checks[check_name]

            if check.is_active(task_vars):
                try:
                    r = check.run(tmp, task_vars)
                except OpenShiftCheckException as e:
                    r = {}
                    r["failed"] = True
                    r["msg"] = str(e)
            else:
                r = {"skipped": True}

            check_results[check_name] = r

            if r.get("failed", False):
                result["failed"] = True
                result["msg"] = "One or more checks failed"

        result["changed"] = any(r.get("changed", False) for r in check_results.values())
        return result

    def load_known_checks(self):
        known_checks = {}

        known_check_classes = set(cls for cls in OpenShiftCheck.subclasses())

        for cls in known_check_classes:
            check_name = cls.name
            if check_name in known_checks:
                other_cls = known_checks[check_name].__class__
                raise OpenShiftCheckException(
                    "non-unique check name '{}' in: '{}.{}' and '{}.{}'".format(
                        check_name,
                        cls.__module__, cls.__name__,
                        other_cls.__module__, other_cls.__name__))
            known_checks[check_name] = cls(module_executor=self._execute_module)

        return known_checks


def resolve_checks(names, all_checks):
    """Returns a set of resolved check names.

    Resolving a check name involves expanding tag references (e.g., '@tag') with
    all the checks that contain the given tag.

    names should be a sequence of strings.

    all_checks should be a sequence of check classes/instances.
    """
    resolved = set()
    for name in names:
        if name.startswith("@"):
            for check in all_checks:
                if name[1:] in check.tags:
                    resolved.add(check.name)
        else:
            resolved.add(name)
    return resolved
