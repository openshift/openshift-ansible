import pytest

from openshift_checks import OpenShiftCheckException
from openshift_checks.docker_storage import DockerStorage


def dummy_check(execute_module=None):
    def dummy_exec(self, status, task_vars):
        raise Exception("dummy executor called")
    return DockerStorage(execute_module=execute_module or dummy_exec)


@pytest.mark.parametrize('is_containerized, group_names, is_active', [
    (False, ["masters", "etcd"], False),
    (False, ["masters", "nodes"], True),
    (True, ["etcd"], True),
])
def test_is_active(is_containerized, group_names, is_active):
    task_vars = dict(
        openshift=dict(common=dict(is_containerized=is_containerized)),
        group_names=group_names,
    )
    assert DockerStorage.is_active(task_vars=task_vars) == is_active


non_atomic_task_vars = {"openshift": {"common": {"is_atomic": False}}}


@pytest.mark.parametrize('docker_info, failed, expect_msg', [
    (
        dict(failed=True, msg="Error connecting: Error while fetching server API version"),
        True,
        ["Is docker running on this host?"],
    ),
    (
        dict(msg="I have no info"),
        True,
        ["missing info"],
    ),
    (
        dict(info={
            "Driver": "devicemapper",
            "DriverStatus": [("Pool Name", "docker-docker--pool")],
        }),
        False,
        [],
    ),
    (
        dict(info={
            "Driver": "devicemapper",
            "DriverStatus": [("Data loop file", "true")],
        }),
        True,
        ["loopback devices with the Docker devicemapper storage driver"],
    ),
    (
        dict(info={
            "Driver": "overlay2",
            "DriverStatus": []
        }),
        False,
        [],
    ),
    (
        dict(info={
            "Driver": "overlay",
        }),
        True,
        ["unsupported Docker storage driver"],
    ),
    (
        dict(info={
            "Driver": "unsupported",
        }),
        True,
        ["unsupported Docker storage driver"],
    ),
])
def test_check_storage_driver(docker_info, failed, expect_msg):
    def execute_module(module_name, module_args, tmp=None, task_vars=None):
        if module_name == "yum":
            return {}
        if module_name != "docker_info":
            raise ValueError("not expecting module " + module_name)
        return docker_info

    check = dummy_check(execute_module=execute_module)
    check._check_dm_usage = lambda status, task_vars: dict()  # stub out for this test
    result = check.run(tmp=None, task_vars=non_atomic_task_vars)

    if failed:
        assert result["failed"]
    else:
        assert not result.get("failed", False)

    for word in expect_msg:
        assert word in result["msg"]


enough_space = {
    "Pool Name": "docker--vg-docker--pool",
    "Data Space Used": "19.92 MB",
    "Data Space Total": "8.535 GB",
    "Metadata Space Used": "40.96 kB",
    "Metadata Space Total": "25.17 MB",
}

not_enough_space = {
    "Pool Name": "docker--vg-docker--pool",
    "Data Space Used": "10 GB",
    "Data Space Total": "10 GB",
    "Metadata Space Used": "42 kB",
    "Metadata Space Total": "43 kB",
}


@pytest.mark.parametrize('task_vars, driver_status, vg_free, success, expect_msg', [
    (
        {"max_thinpool_data_usage_percent": "not a float"},
        enough_space,
        "12g",
        False,
        ["is not a percentage"],
    ),
    (
        {},
        {},  # empty values from driver status
        "bogus",  # also does not parse as bytes
        False,
        ["Could not interpret", "as bytes"],
    ),
    (
        {},
        enough_space,
        "12.00g",
        True,
        [],
    ),
    (
        {},
        not_enough_space,
        "0.00",
        False,
        ["data usage", "metadata usage", "higher than threshold"],
    ),
])
def test_dm_usage(task_vars, driver_status, vg_free, success, expect_msg):
    check = dummy_check()
    check._get_vg_free = lambda pool, task_vars: vg_free
    result = check._check_dm_usage(driver_status, task_vars)
    result_success = not result.get("failed")

    assert result_success is success
    for msg in expect_msg:
        assert msg in result["msg"]


@pytest.mark.parametrize('pool, command_returns, raises, returns', [
    (
        "foo-bar",
        {  # vgs missing
            "msg": "[Errno 2] No such file or directory",
            "failed": True,
            "cmd": "/sbin/vgs",
            "rc": 2,
        },
        "Failed to run /sbin/vgs",
        None,
    ),
    (
        "foo",  # no hyphen in name - should not happen
        {},
        "name does not have the expected format",
        None,
    ),
    (
        "foo-bar",
        dict(stdout="  4.00g\n"),
        None,
        "4.00g",
    ),
    (
        "foo-bar",
        dict(stdout="\n"),  # no matching VG
        "vgs did not find this VG",
        None,
    )
])
def test_vg_free(pool, command_returns, raises, returns):
    def execute_module(module_name, module_args, tmp=None, task_vars=None):
        if module_name != "command":
            raise ValueError("not expecting module " + module_name)
        return command_returns

    check = dummy_check(execute_module=execute_module)
    if raises:
        with pytest.raises(OpenShiftCheckException) as err:
            check._get_vg_free(pool, {})
        assert raises in str(err.value)
    else:
        ret = check._get_vg_free(pool, {})
        assert ret == returns


@pytest.mark.parametrize('string, expect_bytes', [
    ("12", 12.0),
    ("12 k", 12.0 * 1024),
    ("42.42 MB", 42.42 * 1024**2),
    ("12g", 12.0 * 1024**3),
])
def test_convert_to_bytes(string, expect_bytes):
    got = DockerStorage._convert_to_bytes(string)
    assert got == expect_bytes


@pytest.mark.parametrize('string', [
    "bork",
    "42 Qs",
])
def test_convert_to_bytes_error(string):
    with pytest.raises(ValueError) as err:
        DockerStorage._convert_to_bytes(string)
    assert "Cannot convert" in str(err.value)
    assert string in str(err.value)
