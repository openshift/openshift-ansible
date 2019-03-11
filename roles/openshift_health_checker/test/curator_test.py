import pytest

from openshift_checks.logging.curator import Curator, OpenShiftCheckException


plain_curator_pod = {
    "metadata": {
        "labels": {"component": "curator", "deploymentconfig": "logging-curator"},
        "name": "logging-curator",
    },
    "status": {
        "containerStatuses": [{"ready": True}],
        "conditions": [{"status": "True", "type": "Ready"}],
        "podIP": "10.10.10.10",
    }
}


def test_get_curator_pods():
    check = Curator()
    check.get_cronjobs_for_component = lambda *_: [plain_curator_pod]
    result = check.run()
    assert "failed" not in result or not result["failed"]


@pytest.mark.parametrize('cronjobs, expect_error', [
    (
        [],
        'MissingComponentCronJobs',
    ),
])
def test_get_curator_pods_fail(cronjobs, expect_error):
    check = Curator()
    check.get_cronjobs_for_component = lambda *_: cronjobs
    with pytest.raises(OpenShiftCheckException) as excinfo:
        check.run()
    assert excinfo.value.name == expect_error
