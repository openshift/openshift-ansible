import json

import pytest

from openshift_checks.logging.logging_index_time import LoggingIndexTime, OpenShiftCheckException


SAMPLE_UUID = "unique-test-uuid"


def canned_podlogquerytime(exec_oc=None):
    """Create a check object with a canned exec_oc method"""
    check = LoggingIndexTime("dummy")  # fails if a module is actually invoked
    if exec_oc:
        check.oc_cmd = exec_oc
    return check


plain_running_elasticsearch_pod = {
    "metadata": {
        "labels": {"component": "es", "deploymentconfig": "logging-es-data-master"},
        "name": "logging-es-data-master-1",
    },
    "status": {
        "containerStatuses": [{"ready": True}, {"ready": True}],
        "phase": "Running",
    }
}
plain_running_kibana_pod = {
    "metadata": {
        "labels": {"component": "kibana", "deploymentconfig": "logging-kibana"},
        "name": "logging-kibana-1",
    },
    "status": {
        "containerStatuses": [{"ready": True}, {"ready": True}],
        "phase": "Running",
    }
}
not_running_kibana_pod = {
    "metadata": {
        "labels": {"component": "kibana", "deploymentconfig": "logging-kibana"},
        "name": "logging-kibana-2",
    },
    "status": {
        "containerStatuses": [{"ready": True}, {"ready": False}],
        "conditions": [{"status": "True", "type": "Ready"}],
        "phase": "pending",
    }
}


@pytest.mark.parametrize('pods, expect_pods', [
    (
        [not_running_kibana_pod],
        [],
    ),
    (
        [plain_running_kibana_pod],
        [plain_running_kibana_pod],
    ),
    (
        [],
        [],
    )
])
def test_check_running_pods(pods, expect_pods):
    check = canned_podlogquerytime(None)
    pods = check.running_pods(pods)
    assert pods == expect_pods


@pytest.mark.parametrize('name, json_response, uuid, timeout, expect_exception, extra_words', [
    (
        'invalid json response',
        {
            "invalid_field": 1,
        },
        SAMPLE_UUID,
        0.001,
        OpenShiftCheckException,
        ["invalid response", "Elasticsearch"],
    ),
    (
        'empty response',
        {},
        SAMPLE_UUID,
        0.001,
        OpenShiftCheckException,
        ["invalid response", "Elasticsearch"],
    ),
    (
        'valid count in response',
        {
            "count": 1,
        },
        SAMPLE_UUID,
        0.001,
        None,
        [],
    ),
    (
        'valid response but invalid match count',
        {
            "count": 0,
        },
        SAMPLE_UUID,
        0.005,
        OpenShiftCheckException,
        ["expecting match", SAMPLE_UUID, "0.005s"],
    )
], ids=lambda argval: argval[0])
def test_wait_until_cmd_or_err(name, json_response, uuid, timeout, expect_exception, extra_words):
    def exec_oc(exec_cmd, args, task_vars):
        return json.dumps(json_response)

    check = canned_podlogquerytime(exec_oc)

    error = ""
    if expect_exception:
        with pytest.raises(expect_exception) as error:
            check.wait_until_cmd_or_err(plain_running_elasticsearch_pod, uuid, timeout, None)
    else:
        check.wait_until_cmd_or_err(plain_running_elasticsearch_pod, uuid, timeout, None)

    if not expect_exception:
        assert not error

    for word in extra_words:
        assert word in str(error)


@pytest.mark.parametrize('name, json_response, uuid, expect_exception, extra_words', [
    (
        'invalid json response',
        {
            "invalid_field": "invalid",
        },
        SAMPLE_UUID,
        OpenShiftCheckException,
        ["invalid response returned", 'Missing "statusCode" key'],
    ),
    (
        'wrong error code in response',
        {
            "statusCode": 500,
        },
        SAMPLE_UUID,
        OpenShiftCheckException,
        ["Expecting error code", "500"],
    ),
    (
        'correct response code, found unique id is returned',
        {
            "statusCode": 404,
        },
        "sample unique id",
        None,
        ["sample unique id"],
    ),
])
def test_curl_kibana_with_uuid(name, json_response, uuid, expect_exception, extra_words):
    def exec_oc(exec_cmd, args, task_vars):
        return json.dumps(json_response)

    check = canned_podlogquerytime(exec_oc)
    check.generate_uuid = lambda: uuid

    error = ""
    result = ""
    if expect_exception:
        with pytest.raises(expect_exception) as error:
            check.curl_kibana_with_uuid(plain_running_kibana_pod, None)
    else:
        result = check.curl_kibana_with_uuid(plain_running_kibana_pod, None)

    if not expect_exception:
        assert not error

    for word in extra_words:
        if error:
            assert word in str(error)
        elif result:
            assert word in result
