import pytest
import json

from openshift_checks.logging.fluentd import Fluentd


def canned_fluentd(exec_oc=None):
    """Create a Fluentd check object with canned exec_oc method"""
    check = Fluentd("dummy")  # fails if a module is actually invoked
    if exec_oc:
        check._exec_oc = exec_oc
    return check


def assert_error(error, expect_error):
    if expect_error:
        assert error
        assert expect_error in error
    else:
        assert not error


fluentd_pod_node1 = {
    "metadata": {
        "labels": {"component": "fluentd", "deploymentconfig": "logging-fluentd"},
        "name": "logging-fluentd-1",
    },
    "spec": {"host": "node1", "nodeName": "node1"},
    "status": {
        "containerStatuses": [{"ready": True}],
        "conditions": [{"status": "True", "type": "Ready"}],
    }
}
fluentd_pod_node2_down = {
    "metadata": {
        "labels": {"component": "fluentd", "deploymentconfig": "logging-fluentd"},
        "name": "logging-fluentd-2",
    },
    "spec": {"host": "node2", "nodeName": "node2"},
    "status": {
        "containerStatuses": [{"ready": False}],
        "conditions": [{"status": "False", "type": "Ready"}],
    }
}
fluentd_node1 = {
    "metadata": {
        "labels": {"logging-infra-fluentd": "true", "kubernetes.io/hostname": "node1"},
        "name": "node1",
    },
    "status": {"addresses": [{"type": "InternalIP", "address": "10.10.1.1"}]},
}
fluentd_node2 = {
    "metadata": {
        "labels": {"logging-infra-fluentd": "true", "kubernetes.io/hostname": "hostname"},
        "name": "node2",
    },
    "status": {"addresses": [{"type": "InternalIP", "address": "10.10.1.2"}]},
}
fluentd_node3_unlabeled = {
    "metadata": {
        "labels": {"kubernetes.io/hostname": "hostname"},
        "name": "node3",
    },
    "status": {"addresses": [{"type": "InternalIP", "address": "10.10.1.3"}]},
}


@pytest.mark.parametrize('pods, nodes, expect_error', [
    (
        [],
        [],
        'No nodes appear to be defined',
    ),
    (
        [],
        [fluentd_node3_unlabeled],
        'There are no nodes with the fluentd label',
    ),
    (
        [],
        [fluentd_node1, fluentd_node3_unlabeled],
        'Fluentd will not aggregate logs from these nodes.',
    ),
    (
        [],
        [fluentd_node2],
        "nodes are supposed to have a Fluentd pod but do not",
    ),
    (
        [fluentd_pod_node1, fluentd_pod_node1],
        [fluentd_node1],
        'more Fluentd pods running than nodes labeled',
    ),
    (
        [fluentd_pod_node2_down],
        [fluentd_node2],
        "Fluentd pods are supposed to be running",
    ),
    (
        [fluentd_pod_node1],
        [fluentd_node1],
        None,
    ),
])
def test_get_fluentd_pods(pods, nodes, expect_error):
    check = canned_fluentd(lambda cmd, args, task_vars: json.dumps(dict(items=nodes)))

    error = check.check_fluentd(pods, {})
    assert_error(error, expect_error)
