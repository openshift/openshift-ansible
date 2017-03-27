import pytest

from openshift_health_check import resolve_checks


class FakeCheck(object):
    def __init__(self, name, tags=None):
        self.name = name
        self.tags = tags or []


@pytest.mark.parametrize('names,all_checks,expected', [
    ([], [], set()),
    (
        ['a', 'b'],
        [
            FakeCheck('a'),
            FakeCheck('b'),
        ],
        set(['a', 'b']),
    ),
    (
        ['a', 'b', '@group'],
        [
            FakeCheck('from_group_1', ['group', 'another_group']),
            FakeCheck('not_in_group', ['another_group']),
            FakeCheck('from_group_2', ['preflight', 'group']),
            FakeCheck('a'),
            FakeCheck('b'),
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
            FakeCheck('from_group_1', ['group', 'another_group']),
            FakeCheck('not_in_group', ['another_group']),
            FakeCheck('from_group_2', ['preflight', 'group']),
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
