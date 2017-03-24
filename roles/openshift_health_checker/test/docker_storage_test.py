import pytest
import json


from openshift_checks.docker_storage import DockerStorage, OpenShiftCheckException


@pytest.mark.parametrize('is_containerized,is_active', [
    (False, False),
    (True, True),
])
def test_is_active(is_containerized, is_active):
    task_vars = dict(
        openshift=dict(common=dict(is_containerized=is_containerized)),
    )
    assert DockerStorage.is_active(task_vars=task_vars) == is_active


@pytest.mark.parametrize('stdout,message,failed,extra_words', [
    (None, "", True, ["no thinpool usage data"]),
    ("", "", False, ["Invalid JSON value returned by lvs command"]),
    (None, "invalid response", True, ["invalid response"]),
    ("invalid", "invalid response", False, ["Invalid JSON value"]),
])
def test_get_lvs_data_with_failed_response(stdout, message, failed, extra_words):
    def execute_module(module_name, args, tmp=None, task_vars=None):
        if module_name != "command":
            return {
                "changed": False,
            }

        response = {
            "stdout": stdout,
            "msg": message,
            "failed": failed,
        }

        if stdout is None:
            response.pop("stdout")

        return response

    task_vars = dict(
        max_thinpool_data_usage_percent=90.0
    )

    check = DockerStorage(execute_module=execute_module)
    with pytest.raises(OpenShiftCheckException) as excinfo:
        check.run(tmp=None, task_vars=task_vars)

    for word in extra_words:
        assert word in str(excinfo.value)


@pytest.mark.parametrize('limit_percent,failed,extra_words', [
    ("90.0", False, []),
    (80.0, False, []),
    ("invalid percent", True, ["Unable to convert", "to float", "invalid percent"]),
    ("90%", True, ["Unable to convert", "to float", "90%"]),
])
def test_invalid_value_for_thinpool_usage_limit(limit_percent, failed, extra_words):
    def execute_module(module_name, args, tmp=None, task_vars=None):
        if module_name != "command":
            return {
                "changed": False,
            }

        return {
            "stdout": json.dumps({
                "report": [
                    {
                        "lv": [
                            {"lv_name": "docker-pool", "vg_name": "docker", "lv_attr": "twi-aot---", "lv_size": "6.95g",
                             "pool_lv": "", "origin": "", "data_percent": "58.96", "metadata_percent": "4.77",
                             "move_pv": "", "mirror_log": "", "copy_percent": "", "convert_lv": ""},
                        ]
                    }
                ]
            }),
            "failed": False,
        }

    task_vars = dict(
        max_thinpool_data_usage_percent=limit_percent
    )

    check = DockerStorage(execute_module=execute_module).run(tmp=None, task_vars=task_vars)

    if failed:
        assert check["failed"]

        for word in extra_words:
            assert word in check["msg"]
    else:
        assert not check.get("failed", False)


def test_get_lvs_data_with_valid_response():
    def execute_module(module_name, args, tmp=None, task_vars=None):
        if module_name != "command":
            return {
                "changed": False,
            }

        return {
            "stdout": json.dumps({
                "report": [
                    {
                        "lv": [
                            {"lv_name": "docker-pool", "vg_name": "docker", "lv_attr": "twi-aot---", "lv_size": "6.95g",
                             "pool_lv": "", "origin": "", "data_percent": "58.96", "metadata_percent": "4.77",
                             "move_pv": "", "mirror_log": "", "copy_percent": "", "convert_lv": ""}
                        ]
                    }
                ]
            })
        }

    task_vars = dict(
        max_thinpool_data_usage_percent="90"
    )

    check = DockerStorage(execute_module=execute_module).run(tmp=None, task_vars=task_vars)
    assert not check.get("failed", False)


@pytest.mark.parametrize('response,extra_words', [
    (
        {
            "report": [{}],
        },
        ["no thinpool usage data"],
    ),
    (
        {
            "report": [
                {
                    "lv": [
                        {"vg_name": "docker", "lv_attr": "twi-aot---", "lv_size": "6.95g",
                         "move_pv": "", "mirror_log": "", "copy_percent": "", "convert_lv": ""}
                    ]
                }
            ],
        },
        ["no thinpool usage data"],
    ),
    (
        {
            "report": [
                {
                    "lv": [],
                }
            ],
        },
        ["no thinpool usage data"],
    ),
    (
        {
            "report": [
                {
                    "lv": [
                        {"lv_name": "docker-pool", "vg_name": "docker", "lv_attr": "twi-aot---", "lv_size": "6.95g",
                         "pool_lv": "", "origin": "", "data_percent": "58.96",
                         "move_pv": "", "mirror_log": "", "copy_percent": "", "convert_lv": ""}
                    ]
                }
            ],
        },
        ["no thinpool usage data"],
    ),
])
def test_get_lvs_data_with_incomplete_response(response, extra_words):
    def execute_module(module_name, args, tmp=None, task_vars=None):
        if module_name != "command":
            return {
                "changed": False,
            }

        return {
            "stdout": json.dumps(response)
        }

    task_vars = dict(
        max_thinpool_data_usage_percent=90.0
    )

    check = DockerStorage(execute_module=execute_module)
    with pytest.raises(OpenShiftCheckException) as excinfo:
        check.run(tmp=None, task_vars=task_vars)

    assert "no thinpool usage data" in str(excinfo.value)


@pytest.mark.parametrize('response,extra_words', [
    (
        {
            "report": [
                {
                    "lv": [
                        {"lv_name": "docker-pool", "vg_name": "docker", "lv_attr": "twi-aot---", "lv_size": "6.95g",
                         "pool_lv": "", "origin": "", "data_percent": "100.0", "metadata_percent": "90.0",
                         "move_pv": "", "mirror_log": "", "copy_percent": "", "convert_lv": ""}
                    ]
                }
            ],
        },
        ["thinpool data usage above maximum threshold"],
    ),
    (
        {
            "report": [
                {
                    "lv": [
                        {"lv_name": "docker-pool", "vg_name": "docker", "lv_attr": "twi-aot---", "lv_size": "6.95g",
                         "pool_lv": "", "origin": "", "data_percent": "10.0", "metadata_percent": "91.0",
                         "move_pv": "", "mirror_log": "", "copy_percent": "", "convert_lv": ""}
                    ]
                }
            ],
        },
        ["thinpool metadata usage above maximum threshold"],
    ),
])
def test_get_lvs_data_with_high_thinpool_usage(response, extra_words):
    def execute_module(module_name, args, tmp=None, task_vars=None):
        if module_name != "command":
            return {
                "changed": False,
            }

        return {
            "stdout": json.dumps(response),
        }

    task_vars = dict(
        max_thinpool_data_usage_percent="90"
    )

    check = DockerStorage(execute_module=execute_module).run(tmp=None, task_vars=task_vars)

    assert check["failed"]
    for word in extra_words:
        assert word in check["msg"]
