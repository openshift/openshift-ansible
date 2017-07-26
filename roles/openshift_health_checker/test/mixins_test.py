import pytest

from openshift_checks import OpenShiftCheck, OpenShiftCheckException
from openshift_checks.mixins import NotContainerizedMixin


class NotContainerizedCheck(NotContainerizedMixin, OpenShiftCheck):
    name = "not_containerized"
    run = NotImplemented


@pytest.mark.parametrize('task_vars,expected', [
    (dict(openshift=dict(common=dict(is_containerized=False))), True),
    (dict(openshift=dict(common=dict(is_containerized=True))), False),
])
def test_is_active(task_vars, expected):
    assert NotContainerizedCheck(None, task_vars).is_active() == expected


def test_is_active_missing_task_vars():
    with pytest.raises(OpenShiftCheckException) as excinfo:
        NotContainerizedCheck().is_active()
    assert 'is_containerized' in str(excinfo.value)
