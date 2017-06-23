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
from ansible.module_utils.six import string_types

# Augment sys.path so that we can import checks from a directory relative to
# this callback plugin.
sys.path.insert(1, os.path.dirname(os.path.dirname(__file__)))

from openshift_checks import OpenShiftCheck, OpenShiftCheckException, load_checks  # noqa: E402


class ActionModule(ActionBase):

    def run(self, tmp=None, task_vars=None):
        result = super(ActionModule, self).run(tmp, task_vars)
        task_vars = task_vars or {}

        # callback plugins cannot read Ansible vars, but we would like
        # zz_failure_summary to have access to certain values. We do so by
        # storing the information we need in the result.
        result['playbook_context'] = task_vars.get('r_openshift_health_checker_playbook_context')

        try:
            known_checks = self.load_known_checks(tmp, task_vars)
            args = self._task.args
            requested_checks = normalize(args.get('checks', []))

            if not requested_checks:
                result['failed'] = True
                result['msg'] = list_known_checks(known_checks)
                return result

            resolved_checks = resolve_checks(requested_checks, known_checks.values())
        except OpenShiftCheckException as e:
            result["failed"] = True
            result["msg"] = str(e)
            return result

        if "openshift" not in task_vars:
            result["failed"] = True
            result["msg"] = "'openshift' is undefined, did 'openshift_facts' run?"
            return result

        result["checks"] = check_results = {}

        user_disabled_checks = normalize(task_vars.get('openshift_disable_check', []))

        for check_name in resolved_checks:
            display.banner("CHECK [{} : {}]".format(check_name, task_vars["ansible_host"]))
            check = known_checks[check_name]

            if not check.is_active():
                r = dict(skipped=True, skipped_reason="Not active for this host")
            elif check_name in user_disabled_checks:
                r = dict(skipped=True, skipped_reason="Disabled by user request")
            else:
                try:
                    r = check.run()
                except OpenShiftCheckException as e:
                    r = dict(
                        failed=True,
                        msg=str(e),
                    )

            if check.changed:
                r["changed"] = True
            check_results[check_name] = r

        result["changed"] = any(r.get("changed") for r in check_results.values())
        if any(r.get("failed") for r in check_results.values()):
            result["failed"] = True
            result["msg"] = "One or more checks failed"

        return result

    def load_known_checks(self, tmp, task_vars):
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
            known_checks[check_name] = cls(execute_module=self._execute_module, tmp=tmp, task_vars=task_vars)
        return known_checks


def list_known_checks(known_checks):
    """Return text listing the existing checks and tags."""
    # TODO: we could include a description of each check by taking it from a
    # check class attribute (e.g., __doc__) when building the message below.
    msg = (
        'This playbook is meant to run health checks, but no checks were '
        'requested. Set the `openshift_checks` variable to a comma-separated '
        'list of check names or a YAML list. Available checks:\n  {}'
    ).format('\n  '.join(sorted(known_checks)))

    tag_checks = defaultdict(list)
    for cls in known_checks.values():
        for tag in cls.tags:
            tag_checks[tag].append(cls.name)
    tags = [
        '@{} = {}'.format(tag, ','.join(sorted(checks)))
        for tag, checks in tag_checks.items()
    ]

    msg += (
        '\n\nTags can be used as a shortcut to select multiple '
        'checks. Available tags and the checks they select:\n  {}'
    ).format('\n  '.join(sorted(tags)))

    return msg


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


def normalize(checks):
    """Return a clean list of check names.

    The input may be a comma-separated string or a sequence. Leading and
    trailing whitespace characters are removed. Empty items are discarded.
    """
    if isinstance(checks, string_types):
        checks = checks.split(',')
    return [name.strip() for name in checks if name.strip()]
