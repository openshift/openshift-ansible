import pytest

from openshift_checks.disk_availability import DiskAvailability, OpenShiftCheckException


@pytest.mark.parametrize('group_names,is_containerized,is_active', [
    (['masters'], False, True),
    # ensure check is skipped on containerized installs
    (['masters'], True, False),
    (['nodes'], False, True),
    (['etcd'], False, True),
    (['masters', 'nodes'], False, True),
    (['masters', 'etcd'], False, True),
    ([], False, False),
    (['lb'], False, False),
    (['nfs'], False, False),
])
def test_is_active(group_names, is_containerized, is_active):
    task_vars = dict(
        group_names=group_names,
        openshift=dict(common=dict(is_containerized=is_containerized)),
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

    for word in 'determine available disk'.split() + extra_words:
        assert word in str(excinfo.value)


@pytest.mark.parametrize('group_names,ansible_mounts', [
    (
        ['masters'],
        [{
            'mount': '/',
            'size_available': 40 * 10**9 + 1,
        }],
    ),
    (
        ['nodes'],
        [{
            'mount': '/',
            'size_available': 15 * 10**9 + 1,
        }],
    ),
    (
        ['etcd'],
        [{
            'mount': '/',
            'size_available': 20 * 10**9 + 1,
        }],
    ),
    (
        ['etcd'],
        [{
            # not enough space on / ...
            'mount': '/',
            'size_available': 0,
        }, {
            # ... but enough on /var
            'mount': '/var',
            'size_available': 20 * 10**9 + 1,
        }],
    ),
])
def test_succeeds_with_recommended_disk_space(group_names, ansible_mounts):
    task_vars = dict(
        group_names=group_names,
        ansible_mounts=ansible_mounts,
    )

    check = DiskAvailability(execute_module=fake_execute_module)
    result = check.run(tmp=None, task_vars=task_vars)

    assert not result.get('failed', False)


@pytest.mark.parametrize('group_names,ansible_mounts,extra_words', [
    (
        ['masters'],
        [{
            'mount': '/',
            'size_available': 1,
        }],
        ['0.0 GB'],
    ),
    (
        ['nodes'],
        [{
            'mount': '/',
            'size_available': 1 * 10**9,
        }],
        ['1.0 GB'],
    ),
    (
        ['etcd'],
        [{
            'mount': '/',
            'size_available': 1,
        }],
        ['0.0 GB'],
    ),
    (
        ['nodes', 'masters'],
        [{
            'mount': '/',
            # enough space for a node, not enough for a master
            'size_available': 15 * 10**9 + 1,
        }],
        ['15.0 GB'],
    ),
    (
        ['etcd'],
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
def test_fails_with_insufficient_disk_space(group_names, ansible_mounts, extra_words):
    task_vars = dict(
        group_names=group_names,
        ansible_mounts=ansible_mounts,
    )

    check = DiskAvailability(execute_module=fake_execute_module)
    result = check.run(tmp=None, task_vars=task_vars)

    assert result['failed']
    for word in 'below recommended'.split() + extra_words:
        assert word in result['msg']


def fake_execute_module(*args):
    raise AssertionError('this function should not be called')
