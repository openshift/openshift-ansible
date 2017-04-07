import pytest

from openshift_checks.disk_availability import DiskAvailability, OpenShiftCheckException


def test_exception_raised_on_empty_ansible_mounts():
    with pytest.raises(OpenShiftCheckException) as excinfo:
        DiskAvailability(execute_module=NotImplementedError).get_openshift_disk_availability([])

    assert "existing volume mounts from ansible_mounts" in str(excinfo.value)


@pytest.mark.parametrize("group_name,size_available", [
    (
        "masters",
        41110980608,
    ),
    (
        "nodes",
        21110980608,
    ),
    (
        "etcd",
        21110980608,
    ),
])
def test_volume_check_with_recommended_diskspace(group_name, size_available):
    result = DiskAvailability(execute_module=NotImplementedError).run(tmp=None, task_vars=dict(
        openshift=dict(common=dict(
            service_type='origin',
            is_containerized=False,
        )),
        group_names=[group_name],
        ansible_mounts=[{
            "mount": "/",
            "size_available": size_available,
        }]
    ))

    assert not result['failed']
    assert not result['msg']


@pytest.mark.parametrize("group_name,size_available", [
    (
        "masters",
        21110980608,
    ),
    (
        "nodes",
        1110980608,
    ),
    (
        "etcd",
        1110980608,
    ),
])
def test_volume_check_with_insufficient_diskspace(group_name, size_available):
    result = DiskAvailability(execute_module=NotImplementedError).run(tmp=None, task_vars=dict(
        openshift=dict(common=dict(
            service_type='origin',
            is_containerized=False,
        )),
        group_names=[group_name],
        ansible_mounts=[{
            "mount": "/",
            "size_available": size_available,
        }]
    ))

    assert result['failed']
    assert "is below recommended storage" in result['msg']


def test_volume_check_with_unsupported_mountpaths():
    result = DiskAvailability(execute_module=NotImplementedError).run(tmp=None, task_vars=dict(
        openshift=dict(common=dict(
            service_type='origin',
            is_containerized=False,
        )),
        group_names=["masters", "nodes"],
        ansible_mounts=[{
            "mount": "/unsupported",
            "size_available": 12345,
        }]
    ))

    assert result['failed']
    assert "0 GB" in result['msg']


def test_volume_check_with_invalid_groupname():
    with pytest.raises(OpenShiftCheckException) as excinfo:
        result = DiskAvailability(execute_module=NotImplementedError).run(tmp=None, task_vars=dict(
            openshift=dict(common=dict(
                service_type='origin',
                is_containerized=False,
            )),
            group_names=["invalid"],
            ansible_mounts=[{
                "mount": "/unsupported",
                "size_available": 12345,
            }]
        ))

    assert "'invalid'" in str(excinfo.value)
