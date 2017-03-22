import pytest

from openshift_checks.logging.curator import Curator


def canned_curator(exec_oc=None):
    """Create a Curator check object with canned exec_oc method"""
    check = Curator("dummy")  # fails if a module is actually invoked
    if exec_oc:
        check._exec_oc = exec_oc
    return check


def assert_error(error, expect_error):
    if expect_error:
        assert error
        assert expect_error in error
    else:
        assert not error


plain_curator_pod = {
    "metadata": {
        "labels": {"component": "curator", "deploymentconfig": "logging-curator"},
        "name": "logging-curator-1",
    },
    "status": {
        "containerStatuses": [{"ready": True}],
        "conditions": [{"status": "True", "type": "Ready"}],
        "podIP": "10.10.10.10",
    }
}

not_running_curator_pod = {
    "metadata": {
        "labels": {"component": "curator", "deploymentconfig": "logging-curator"},
        "name": "logging-curator-2",
    },
    "status": {
        "containerStatuses": [{"ready": False}],
        "conditions": [{"status": "False", "type": "Ready"}],
        "podIP": "10.10.10.10",
    }
}


@pytest.mark.parametrize('pods, expect_error', [
    (
        [],
        "no Curator pods",
    ),
    (
        [plain_curator_pod],
        None,
    ),
    (
        [not_running_curator_pod],
        "not currently in a running state",
    ),
    (
        [plain_curator_pod, plain_curator_pod],
        "more than one Curator pod",
    ),
])
def test_get_curator_pods(pods, expect_error):
    check = canned_curator()
    error = check.check_curator(pods)
    assert_error(error, expect_error)
