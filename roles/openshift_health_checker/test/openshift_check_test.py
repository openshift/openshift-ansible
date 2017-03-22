import pytest

from openshift_checks import OpenShiftCheck, OpenShiftCheckException
from openshift_checks import load_checks, get_var


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


def test_OpenShiftCheck_init():
    class TestCheck(OpenShiftCheck):
        name = "test_check"
        run = NotImplemented

    # initialization requires at least one argument (apart from self)
    with pytest.raises(TypeError) as excinfo:
        TestCheck()
    assert 'execute_module' in str(excinfo.value)
    assert 'module_executor' in str(excinfo.value)

    execute_module = object()

    # initialize with positional argument
    check = TestCheck(execute_module)
    # new recommended name
    assert check.execute_module == execute_module
    # deprecated attribute name
    assert check.module_executor == execute_module

    # initialize with keyword argument, recommended name
    check = TestCheck(execute_module=execute_module)
    # new recommended name
    assert check.execute_module == execute_module
    # deprecated attribute name
    assert check.module_executor == execute_module

    # initialize with keyword argument, deprecated name
    check = TestCheck(module_executor=execute_module)
    # new recommended name
    assert check.execute_module == execute_module
    # deprecated attribute name
    assert check.module_executor == execute_module


def test_subclasses():
    """OpenShiftCheck.subclasses should find all subclasses recursively."""
    class TestCheck1(OpenShiftCheck):
        pass

    class TestCheck2(OpenShiftCheck):
        pass

    class TestCheck1A(TestCheck1):
        pass

    local_subclasses = set([TestCheck1, TestCheck1A, TestCheck2])
    known_subclasses = set(OpenShiftCheck.subclasses())

    assert local_subclasses - known_subclasses == set(), "local_subclasses should be a subset of known_subclasses"


def test_load_checks():
    """Loading checks should load and return Python modules."""
    modules = load_checks()
    assert modules


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
