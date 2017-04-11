import pytest

from openshift_checks.memory_availability import MemoryAvailability


@pytest.mark.parametrize('group_names,is_active', [
    (['masters'], True),
    (['nodes'], True),
    (['etcd'], True),
    (['masters', 'nodes'], True),
    (['masters', 'etcd'], True),
    ([], False),
    (['lb'], False),
    (['nfs'], False),
])
def test_is_active(group_names, is_active):
    task_vars = dict(
        group_names=group_names,
    )
    assert MemoryAvailability.is_active(task_vars=task_vars) == is_active


@pytest.mark.parametrize('group_names,ansible_memtotal_mb', [
    (
        ['masters'],
        17200,
    ),
    (
        ['nodes'],
        8200,
    ),
    (
        ['etcd'],
        22200,
    ),
    (
        ['masters', 'nodes'],
        17000,
    ),
])
def test_succeeds_with_recommended_memory(group_names, ansible_memtotal_mb):
    task_vars = dict(
        group_names=group_names,
        ansible_memtotal_mb=ansible_memtotal_mb,
    )

    check = MemoryAvailability(execute_module=fake_execute_module)
    result = check.run(tmp=None, task_vars=task_vars)

    assert not result.get('failed', False)


@pytest.mark.parametrize('group_names,ansible_memtotal_mb,extra_words', [
    (
        ['masters'],
        0,
        ['0.0 GB'],
    ),
    (
        ['nodes'],
        100,
        ['0.1 GB'],
    ),
    (
        ['etcd'],
        -1,
        ['0.0 GB'],
    ),
    (
        ['nodes', 'masters'],
        # enough memory for a node, not enough for a master
        11000,
        ['11.0 GB'],
    ),
])
def test_fails_with_insufficient_memory(group_names, ansible_memtotal_mb, extra_words):
    task_vars = dict(
        group_names=group_names,
        ansible_memtotal_mb=ansible_memtotal_mb,
    )

    check = MemoryAvailability(execute_module=fake_execute_module)
    result = check.run(tmp=None, task_vars=task_vars)

    assert result['failed']
    for word in 'below recommended'.split() + extra_words:
        assert word in result['msg']


def fake_execute_module(*args):
    raise AssertionError('this function should not be called')
