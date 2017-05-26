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


@pytest.mark.parametrize('group_names,configured_min,ansible_memtotal_mb', [
    (
        ['masters'],
        0,
        17200,
    ),
    (
        ['nodes'],
        0,
        8200,
    ),
    (
        ['nodes'],
        1,  # configure lower threshold
        2000,  # too low for recommended but not for configured
    ),
    (
        ['nodes'],
        2,  # configure threshold where adjustment pushes it over
        1900,
    ),
    (
        ['etcd'],
        0,
        8200,
    ),
    (
        ['masters', 'nodes'],
        0,
        17000,
    ),
])
def test_succeeds_with_recommended_memory(group_names, configured_min, ansible_memtotal_mb):
    task_vars = dict(
        group_names=group_names,
        openshift_check_min_host_memory_gb=configured_min,
        ansible_memtotal_mb=ansible_memtotal_mb,
    )

    check = MemoryAvailability(execute_module=fake_execute_module)
    result = check.run(tmp=None, task_vars=task_vars)

    assert not result.get('failed', False)


@pytest.mark.parametrize('group_names,configured_min,ansible_memtotal_mb,extra_words', [
    (
        ['masters'],
        0,
        0,
        ['0.0 GiB'],
    ),
    (
        ['nodes'],
        0,
        100,
        ['0.1 GiB'],
    ),
    (
        ['nodes'],
        24,  # configure higher threshold
        20 * 1024,  # enough to meet recommended but not configured
        ['20.0 GiB'],
    ),
    (
        ['nodes'],
        24,  # configure higher threshold
        22 * 1024,  # not enough for adjustment to push over threshold
        ['22.0 GiB'],
    ),
    (
        ['etcd'],
        0,
        6 * 1024,
        ['6.0 GiB'],
    ),
    (
        ['etcd', 'masters'],
        0,
        9 * 1024,  # enough memory for etcd, not enough for a master
        ['9.0 GiB'],
    ),
    (
        ['nodes', 'masters'],
        0,
        # enough memory for a node, not enough for a master
        11 * 1024,
        ['11.0 GiB'],
    ),
])
def test_fails_with_insufficient_memory(group_names, configured_min, ansible_memtotal_mb, extra_words):
    task_vars = dict(
        group_names=group_names,
        openshift_check_min_host_memory_gb=configured_min,
        ansible_memtotal_mb=ansible_memtotal_mb,
    )

    check = MemoryAvailability(execute_module=fake_execute_module)
    result = check.run(tmp=None, task_vars=task_vars)

    assert result.get('failed', False)
    for word in 'below recommended'.split() + extra_words:
        assert word in result['msg']


def fake_execute_module(*args):
    raise AssertionError('this function should not be called')
