import pytest


from openshift_checks.docker_storage_driver import DockerStorageDriver


@pytest.mark.parametrize('is_containerized,is_active', [
    (False, False),
    (True, True),
])
def test_is_active(is_containerized, is_active):
    task_vars = dict(
        openshift=dict(common=dict(is_containerized=is_containerized)),
    )
    assert DockerStorageDriver.is_active(task_vars=task_vars) == is_active


@pytest.mark.parametrize('info,failed,extra_words', [
    (
        {
            "Driver": "devicemapper",
            "DriverStatus": [("Pool Name", "docker-docker--pool")],
        },
        False,
        [],
    ),
    (
        {
            "Driver": "devicemapper",
            "DriverStatus": [("Data loop file", "true")],
        },
        True,
        ["Use of loopback devices is discouraged"],
    ),
    (
        {
            "Driver": "overlay2",
            "DriverStatus": []
        },
        False,
        [],
    ),
    (
        {
            "Driver": "overlay",
        },
        True,
        ["Unsupported Docker storage driver"],
    ),
    (
        {
            "Driver": "unsupported",
        },
        True,
        ["Unsupported Docker storage driver"],
    ),
])
def test_check_storage_driver(info, failed, extra_words):
    def execute_module(module_name, args, tmp=None, task_vars=None):
        if module_name != "docker_info":
            return {
                "changed": False,
            }

        return {
            "info": info
        }

    task_vars = dict(
        openshift=dict(common=dict(is_containerized=True))
    )

    check = DockerStorageDriver(execute_module=execute_module).run(tmp=None, task_vars=task_vars)

    if failed:
        assert check["failed"]
    else:
        assert not check.get("failed", False)

    for word in extra_words:
        assert word in check["msg"]
