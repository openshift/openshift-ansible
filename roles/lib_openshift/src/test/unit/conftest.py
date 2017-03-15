import importlib
import inspect

import pytest

from lib_openshift.library import *  # noqa: F401,F403


def pytest_generate_tests(metafunc):
    if 'binary_lookup_module' in metafunc.fixturenames:
        lookup_modules = []
        ids = []
        for key in list(globals().keys()):
            value = globals()[key]
            if inspect.ismodule(value):
                for func, _ in inspect.getmembers(value, inspect.isfunction):
                    if func == 'locate_oc_binary':
                        lookup_modules.append(value)
                        ids.append(key)
        metafunc.parametrize('binary_lookup_module', lookup_modules, ids=ids)


@pytest.fixture
def mock_tmpfile_copy(request, mocker):
    module_under_test = request.module.MODULE_UNDER_TEST
    patch_method = module_under_test.__name__ + '.Utils.create_tmpfile_copy'
    mocker.patch(patch_method, return_value='/tmp/mocked_kubeconfig')


@pytest.fixture
def mock_locate_binary(request, mocker):
    module_name = request.module.MODULE_UNDER_TEST.__name__
    patch_method = module_name + '.locate_oc_binary'
    mocker.patch(patch_method, return_value='oc')


@pytest.fixture
def mock_run_cmd(request, mocker, mock_locate_binary, mock_tmpfile_copy):
    module_name = request.module.MODULE_UNDER_TEST.__name__
    class_name = request.module.CLASS_UNDER_TEST.__name__
    patch_method = "{}.{}._run".format(module_name, class_name)
    run_cmd = mocker.patch(patch_method)
    yield run_cmd


@pytest.fixture(params=['yaml', 'ruamel.yaml'])
def yaml_provider(request, monkeypatch):
    yaml_module = importlib.import_module(request.param)

    monkeypatch.setattr(request.module.MODULE_UNDER_TEST, 'yaml', yaml_module)
    return yaml_module
