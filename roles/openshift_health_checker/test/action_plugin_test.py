import pytest

from ansible.playbook.play_context import PlayContext

from openshift_health_check import ActionModule, resolve_checks
from openshift_checks import OpenShiftCheckException


def fake_check(name='fake_check', tags=None, is_active=True, run_return=None, run_exception=None):
    """Returns a new class that is compatible with OpenShiftCheck for testing."""

    _name, _tags = name, tags

    class FakeCheck(object):
        name = _name
        tags = _tags or []

        def __init__(self, execute_module=None):
            pass

        @classmethod
        def is_active(cls, task_vars):
            return is_active

        def run(self, tmp, task_vars):
            if run_exception is not None:
                raise run_exception
            return run_return

    return FakeCheck


# Fixtures


@pytest.fixture
def plugin():
    task = FakeTask('openshift_health_check', {'checks': ['fake_check']})
    plugin = ActionModule(task, None, PlayContext(), None, None, None)
    return plugin


class FakeTask(object):
    def __init__(self, action, args):
        self.action = action
        self.args = args
        self.async = 0


@pytest.fixture
def task_vars():
    return dict(openshift=dict(), ansible_host='unit-test-host')


# Assertion helpers


def failed(result, msg_has=None):
    if msg_has is not None:
        assert 'msg' in result
        for term in msg_has:
            assert term.lower() in result['msg'].lower()
    return result.get('failed', False)


def changed(result):
    return result.get('changed', False)


# tests whether task is skipped, not individual checks
def skipped(result):
    return result.get('skipped', False)


# Tests


@pytest.mark.parametrize('task_vars', [
    None,
    {},
])
def test_action_plugin_missing_openshift_facts(plugin, task_vars):
    result = plugin.run(tmp=None, task_vars=task_vars)

    assert failed(result, msg_has=['openshift_facts'])


def test_action_plugin_cannot_load_checks_with_the_same_name(plugin, task_vars, monkeypatch):
    FakeCheck1 = fake_check('duplicate_name')
    FakeCheck2 = fake_check('duplicate_name')
    checks = [FakeCheck1, FakeCheck2]
    monkeypatch.setattr('openshift_checks.OpenShiftCheck.subclasses', classmethod(lambda cls: checks))

    result = plugin.run(tmp=None, task_vars=task_vars)

    assert failed(result, msg_has=['unique', 'duplicate_name', 'FakeCheck'])


def test_action_plugin_skip_non_active_checks(plugin, task_vars, monkeypatch):
    checks = [fake_check(is_active=False)]
    monkeypatch.setattr('openshift_checks.OpenShiftCheck.subclasses', classmethod(lambda cls: checks))

    result = plugin.run(tmp=None, task_vars=task_vars)

    assert result['checks']['fake_check'] == dict(skipped=True, skipped_reason="Not active for this host")
    assert not failed(result)
    assert not changed(result)
    assert not skipped(result)


def test_action_plugin_skip_disabled_checks(plugin, task_vars, monkeypatch):
    checks = [fake_check('fake_check', is_active=True)]
    monkeypatch.setattr('openshift_checks.OpenShiftCheck.subclasses', classmethod(lambda cls: checks))

    task_vars['openshift_disable_check'] = 'fake_check'
    result = plugin.run(tmp=None, task_vars=task_vars)

    assert result['checks']['fake_check'] == dict(skipped=True, skipped_reason="Disabled by user request")
    assert not failed(result)
    assert not changed(result)
    assert not skipped(result)


def test_action_plugin_run_check_ok(plugin, task_vars, monkeypatch):
    check_return_value = {'ok': 'test'}
    check_class = fake_check(run_return=check_return_value)
    monkeypatch.setattr(plugin, 'load_known_checks', lambda: {'fake_check': check_class()})
    monkeypatch.setattr('openshift_health_check.resolve_checks', lambda *args: ['fake_check'])

    result = plugin.run(tmp=None, task_vars=task_vars)

    assert result['checks']['fake_check'] == check_return_value
    assert not failed(result)
    assert not changed(result)
    assert not skipped(result)


def test_action_plugin_run_check_changed(plugin, task_vars, monkeypatch):
    check_return_value = {'ok': 'test', 'changed': True}
    check_class = fake_check(run_return=check_return_value)
    monkeypatch.setattr(plugin, 'load_known_checks', lambda: {'fake_check': check_class()})
    monkeypatch.setattr('openshift_health_check.resolve_checks', lambda *args: ['fake_check'])

    result = plugin.run(tmp=None, task_vars=task_vars)

    assert result['checks']['fake_check'] == check_return_value
    assert not failed(result)
    assert changed(result)
    assert not skipped(result)


def test_action_plugin_run_check_fail(plugin, task_vars, monkeypatch):
    check_return_value = {'failed': True}
    check_class = fake_check(run_return=check_return_value)
    monkeypatch.setattr(plugin, 'load_known_checks', lambda: {'fake_check': check_class()})
    monkeypatch.setattr('openshift_health_check.resolve_checks', lambda *args: ['fake_check'])

    result = plugin.run(tmp=None, task_vars=task_vars)

    assert result['checks']['fake_check'] == check_return_value
    assert failed(result, msg_has=['failed'])
    assert not changed(result)
    assert not skipped(result)


def test_action_plugin_run_check_exception(plugin, task_vars, monkeypatch):
    exception_msg = 'fake check has an exception'
    run_exception = OpenShiftCheckException(exception_msg)
    check_class = fake_check(run_exception=run_exception)
    monkeypatch.setattr(plugin, 'load_known_checks', lambda: {'fake_check': check_class()})
    monkeypatch.setattr('openshift_health_check.resolve_checks', lambda *args: ['fake_check'])

    result = plugin.run(tmp=None, task_vars=task_vars)

    assert failed(result['checks']['fake_check'], msg_has=exception_msg)
    assert failed(result, msg_has=['failed'])
    assert not changed(result)
    assert not skipped(result)


def test_action_plugin_resolve_checks_exception(plugin, task_vars, monkeypatch):
    monkeypatch.setattr(plugin, 'load_known_checks', lambda: {})

    result = plugin.run(tmp=None, task_vars=task_vars)

    assert failed(result, msg_has=['unknown', 'name'])
    assert not changed(result)
    assert not skipped(result)


@pytest.mark.parametrize('names,all_checks,expected', [
    ([], [], set()),
    (
        ['a', 'b'],
        [
            fake_check('a'),
            fake_check('b'),
        ],
        set(['a', 'b']),
    ),
    (
        ['a', 'b', '@group'],
        [
            fake_check('from_group_1', ['group', 'another_group']),
            fake_check('not_in_group', ['another_group']),
            fake_check('from_group_2', ['preflight', 'group']),
            fake_check('a'),
            fake_check('b'),
        ],
        set(['a', 'b', 'from_group_1', 'from_group_2']),
    ),
])
def test_resolve_checks_ok(names, all_checks, expected):
    assert resolve_checks(names, all_checks) == expected


@pytest.mark.parametrize('names,all_checks,words_in_exception,words_not_in_exception', [
    (
        ['testA', 'testB'],
        [],
        ['check', 'name', 'testA', 'testB'],
        ['tag', 'group', '@'],
    ),
    (
        ['@group'],
        [],
        ['tag', 'name', 'group'],
        ['check', '@'],
    ),
    (
        ['testA', 'testB', '@group'],
        [],
        ['check', 'name', 'testA', 'testB', 'tag', 'group'],
        ['@'],
    ),
    (
        ['testA', 'testB', '@group'],
        [
            fake_check('from_group_1', ['group', 'another_group']),
            fake_check('not_in_group', ['another_group']),
            fake_check('from_group_2', ['preflight', 'group']),
        ],
        ['check', 'name', 'testA', 'testB'],
        ['tag', 'group', '@'],
    ),
])
def test_resolve_checks_failure(names, all_checks, words_in_exception, words_not_in_exception):
    with pytest.raises(Exception) as excinfo:
        resolve_checks(names, all_checks)
    for word in words_in_exception:
        assert word in str(excinfo.value)
    for word in words_not_in_exception:
        assert word not in str(excinfo.value)
