import pytest

from openshift_checks.memory_availability import MemoryAvailability, OpenShiftCheckException


@pytest.mark.parametrize('group_names,is_containerized,is_active', [
    (['masters'], False, True),
    # ensure check is skipped on containerized installs
    (['masters'], True, True),
    (['nodes'], True, True),
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
    assert MemoryAvailability.is_active(task_vars=task_vars) == is_active


@pytest.mark.parametrize("group_name,size_available", [
    (
        "masters",
        17200,
    ),
    (
        "nodes",
        8200,
    ),
    (
        "etcd",
        12200,
    ),
])
def test_mem_check_with_recommended_memtotal(group_name, size_available):
    result = MemoryAvailability(execute_module=NotImplementedError).run(tmp=None, task_vars=dict(
        group_names=[group_name],
        ansible_memtotal_mb=size_available,
    ))

    assert not result.get('failed', False)


@pytest.mark.parametrize("group_name,size_available", [
    (
        "masters",
        1,
    ),
    (
        "nodes",
        2,
    ),
    (
        "etcd",
        3,
    ),
])
def test_mem_check_with_insufficient_memtotal(group_name, size_available):
    result = MemoryAvailability(execute_module=NotImplementedError).run(tmp=None, task_vars=dict(
        group_names=[group_name],
        ansible_memtotal_mb=size_available,
    ))

    assert result['failed']
    assert "below recommended storage" in result['msg']


def test_mem_check_with_invalid_groupname():
    with pytest.raises(OpenShiftCheckException) as excinfo:
        result = MemoryAvailability(execute_module=NotImplementedError).run(tmp=None, task_vars=dict(
            openshift=dict(common=dict(
                service_type='origin',
                is_containerized=False,
            )),
            group_names=["invalid"],
            ansible_memtotal_mb=1234567,
        ))

    assert "'invalid'" in str(excinfo.value)
