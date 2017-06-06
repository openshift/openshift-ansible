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
    assert DiskAvailability(None, task_vars).is_active() == is_active


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

    with pytest.raises(OpenShiftCheckException) as excinfo:
        DiskAvailability(fake_execute_module, task_vars).run()

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

    result = DiskAvailability(fake_execute_module, task_vars).run()

    assert not result.get('failed', False)


@pytest.mark.parametrize('name,group_names,configured_min,ansible_mounts,extra_words', [
    (
        'test with no space available',
        ['masters'],
        0,
        [{
            'mount': '/',
            'size_available': 1,
        }],
        ['0.0 GB'],
    ),
    (
        'test with a higher configured required value',
        ['masters'],
        100,  # set a higher threshold
        [{
            'mount': '/',
            'size_available': 50 * 10**9,  # would normally be enough...
        }],
        ['100.0 GB'],
    ),
    (
        'test with 1GB available, but "0" GB space requirement',
        ['nodes'],
        0,
        [{
            'mount': '/',
            'size_available': 1 * 10**9,
        }],
        ['1.0 GB'],
    ),
    (
        'test with no space available, but "0" GB space requirement',
        ['etcd'],
        0,
        [{
            'mount': '/',
            'size_available': 1,
        }],
        ['0.0 GB'],
    ),
    (
        'test with enough space for a node, but not for a master',
        ['nodes', 'masters'],
        0,
        [{
            'mount': '/',
            'size_available': 15 * 10**9 + 1,
        }],
        ['15.0 GB'],
    ),
    (
        'test failure with enough space on "/", but not enough on "/var"',
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
], ids=lambda argval: argval[0])
def test_fails_with_insufficient_disk_space(name, group_names, configured_min, ansible_mounts, extra_words):
    task_vars = dict(
        group_names=group_names,
        openshift_check_min_host_disk_gb=configured_min,
        ansible_mounts=ansible_mounts,
    )

    result = DiskAvailability(fake_execute_module, task_vars).run()

    assert result['failed']
    for word in 'below recommended'.split() + extra_words:
        assert word in result.get('msg', '')


@pytest.mark.parametrize('name,group_names,context,ansible_mounts,failed,extra_words', [
    (
        'test without enough space for master under "upgrade" context',
        ['nodes', 'masters'],
        "upgrade",
        [{
            'mount': '/',
            'size_available': 1 * 10**9 + 1,
            'size_total': 21 * 10**9 + 1,
        }],
        True,
        ["1.0 GB"],
    ),
    (
        'test with enough space for master under "upgrade" context',
        ['nodes', 'masters'],
        "upgrade",
        [{
            'mount': '/',
            'size_available': 10 * 10**9 + 1,
            'size_total': 21 * 10**9 + 1,
        }],
        False,
        [],
    ),
    (
        'test with not enough space for master, and non-upgrade context',
        ['nodes', 'masters'],
        "health",
        [{
            'mount': '/',
            # not enough space for a master,
            # "health" context should not lower requirement
            'size_available': 20 * 10**9 + 1,
        }],
        True,
        ["20.0 GB", "below minimum"],
    ),
], ids=lambda argval: argval[0])
def test_min_required_space_changes_with_upgrade_context(name, group_names, context, ansible_mounts, failed, extra_words):
    task_vars = dict(
        r_openshift_health_checker_playbook_context=context,
        group_names=group_names,
        ansible_mounts=ansible_mounts,
    )

    check = DiskAvailability(execute_module=fake_execute_module)
    result = check.run(tmp=None, task_vars=task_vars)

    assert result.get("failed", False) == failed
    for word in extra_words:
        assert word in result.get('msg', '')


def fake_execute_module(*args):
    raise AssertionError('this function should not be called')
