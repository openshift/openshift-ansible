import pytest

from openshift_checks.disk_availability import DiskAvailability, OpenShiftCheckException


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
    assert DiskAvailability.is_active(task_vars=task_vars) == is_active


@pytest.mark.parametrize('ansible_mounts,extra_words', [
    ([], ['none']),  # empty ansible_mounts
    ([{'mount': '/mnt'}], ['/mnt']),  # missing relevant mount paths
    ([{'mount': '/var'}], ['/var']),  # missing size_available
])
def test_cannot_determine_available_disk(ansible_mounts, extra_words):
    task_vars = dict(
        group_names=['masters'],
        ansible_mounts=ansible_mounts,
    )
    check = DiskAvailability(execute_module=fake_execute_module)

    with pytest.raises(OpenShiftCheckException) as excinfo:
        check.run(tmp=None, task_vars=task_vars)

    for word in 'determine disk availability'.split() + extra_words:
        assert word in str(excinfo.value)


@pytest.mark.parametrize('group_names,configured_min,ansible_mounts', [
    (
        ['masters'],
        0,
        [{
            'mount': '/',
            'size_available': 40 * 10**9 + 1,
        }],
    ),
    (
        ['nodes'],
        0,
        [{
            'mount': '/',
            'size_available': 15 * 10**9 + 1,
        }],
    ),
    (
        ['etcd'],
        0,
        [{
            'mount': '/',
            'size_available': 20 * 10**9 + 1,
        }],
    ),
    (
        ['etcd'],
        1,  # configure lower threshold
        [{
            'mount': '/',
            'size_available': 1 * 10**9 + 1,  # way smaller than recommended
        }],
    ),
    (
        ['etcd'],
        0,
        [{
            # not enough space on / ...
            'mount': '/',
            'size_available': 2 * 10**9,
        }, {
            # ... but enough on /var
            'mount': '/var',
            'size_available': 20 * 10**9 + 1,
        }],
    ),
])
def test_succeeds_with_recommended_disk_space(group_names, configured_min, ansible_mounts):
    task_vars = dict(
        group_names=group_names,
        openshift_check_min_host_disk_gb=configured_min,
        ansible_mounts=ansible_mounts,
    )

    check = DiskAvailability(execute_module=fake_execute_module)
    result = check.run(tmp=None, task_vars=task_vars)

    assert not result.get('failed', False)


@pytest.mark.parametrize('group_names,configured_min,ansible_mounts,extra_words', [
    (
        ['masters'],
        0,
        [{
            'mount': '/',
            'size_available': 1,
        }],
        ['0.0 GB'],
    ),
    (
        ['masters'],
        100,  # set a higher threshold
        [{
            'mount': '/',
            'size_available': 50 * 10**9,  # would normally be enough...
        }],
        ['100.0 GB'],
    ),
    (
        ['nodes'],
        0,
        [{
            'mount': '/',
            'size_available': 1 * 10**9,
        }],
        ['1.0 GB'],
    ),
    (
        ['etcd'],
        0,
        [{
            'mount': '/',
            'size_available': 1,
        }],
        ['0.0 GB'],
    ),
    (
        ['nodes', 'masters'],
        0,
        [{
            'mount': '/',
            # enough space for a node, not enough for a master
            'size_available': 15 * 10**9 + 1,
        }],
        ['15.0 GB'],
    ),
    (
        ['etcd'],
        0,
        [{
            # enough space on / ...
            'mount': '/',
            'size_available': 20 * 10**9 + 1,
        }, {
            # .. but not enough on /var
            'mount': '/var',
            'size_available': 0,
        }],
        ['0.0 GB'],
    ),
])
def test_fails_with_insufficient_disk_space(group_names, configured_min, ansible_mounts, extra_words):
    task_vars = dict(
        group_names=group_names,
        openshift_check_min_host_disk_gb=configured_min,
        ansible_mounts=ansible_mounts,
    )

    check = DiskAvailability(execute_module=fake_execute_module)
    result = check.run(tmp=None, task_vars=task_vars)

    assert result['failed']
    for word in 'below recommended'.split() + extra_words:
        assert word in result['msg']


def fake_execute_module(*args):
    raise AssertionError('this function should not be called')
