import pytest

from openshift_checks import get_var, OpenShiftCheckException


# Fixtures


@pytest.fixture()
def task_vars():
    return dict(foo=42, bar=dict(baz="openshift"))


@pytest.fixture(params=[
    ("notfound",),
    ("multiple", "keys", "not", "in", "task_vars"),
])
def missing_keys(request):
    return request.param


# Tests


@pytest.mark.parametrize("keys,expected", [
    (("foo",), 42),
    (("bar", "baz"), "openshift"),
])
def test_get_var_ok(task_vars, keys, expected):
    assert get_var(task_vars, *keys) == expected


def test_get_var_error(task_vars, missing_keys):
    with pytest.raises(OpenShiftCheckException):
        get_var(task_vars, *missing_keys)


def test_get_var_default(task_vars, missing_keys):
    default = object()
    assert get_var(task_vars, *missing_keys, default=default) == default
