'''
 Unit tests for oc secret add
'''
import copy
import json
import os
import six
import sys
import mock

import pytest

# Removing invalid variable names for tests so that I can
# keep them brief
# pylint: disable=invalid-name,no-name-in-module
# Disable import-error b/c our libraries aren't loaded in jenkins
# pylint: disable=import-error,wrong-import-position
# place class in our python path
MODULE_PATH = os.path.realpath(os.path.join(os.path.dirname(__file__), os.pardir,
                                            os.pardir, os.pardir, 'library'))
sys.path.insert(1, MODULE_PATH)
import oc_serviceaccount_secret  # noqa: E402


@pytest.fixture(params=['PyYAML', 'ruamel.yaml'])
def yaml_provider(request, monkeypatch):
    if request.param == 'PyYAML':
        import yaml as yaml_module
    else:
        import ruamel.yaml as yaml_module

    monkeypatch.setattr(oc_serviceaccount_secret, 'yaml', yaml_module)
    return yaml_module


@pytest.fixture
def builder():
    return {
        'apiVersion': 'v1',
        'imagePullSecrets': [{'name': 'builder-dockercfg-rsrua'}],
        'kind': 'ServiceAccount',
        'metadata': {
            'creationTimestamp': '2017-02-05T17:02:00Z',
            'name': 'builder',
            'namespace': 'default',
            'resourceVersion': '302879',
            'selfLink': '/api/v1/namespaces/default/serviceaccounts/builder',
            'uid': 'cf47bca7-ebc4-11e6-b041-0ed9df7abc38'
        },
        'secrets': [
            {'name': 'builder-dockercfg-rsrua'},
            {'name': 'builder-token-akqxi'},
        ]
    }


@pytest.fixture
def service_account():
    return {
        "apiVersion": "v1",
        "imagePullSecrets": [{"name": "builder-dockercfg-rsrua"}],
        "kind": "ServiceAccount",
        "metadata": {
            "name": "builder",
            "namespace": "default",
            "selfLink": "/api/v1/namespaces/default/serviceaccounts/builder",
            "uid": "cf47bca7-ebc4-11e6-b041-0ed9df7abc38",
            "resourceVersion": "302879",
            "creationTimestamp": "2017-02-05T17:02:00Z"
        },
        "secrets": [
            {"name": "builder-dockercfg-rsrua"},
            {"name": "builder-token-akqxi"}
        ]
    }


def test_adding_a_secret_to_a_serviceaccount(yaml_provider, mocker, service_account, builder):
    ''' Testing adding a secret to a service account '''
    mocker.patch('oc_serviceaccount_secret.locate_oc_binary', return_value='oc')
    mocker.patch('oc_serviceaccount_secret.Utils.create_tmpfile_copy', return_value='/tmp/mocked_kubeconfig')
    spy_write = mocker.spy(oc_serviceaccount_secret.Yedit, '_write')
    # Arrange

    # run_ansible input parameters
    params = {
        'state': 'present',
        'namespace': 'default',
        'secret': 'newsecret',
        'service_account': 'builder',
        'kubeconfig': '/etc/origin/master/admin.kubeconfig',
        'debug': False,
    }

    new_secret = {'name': 'newsecret'}

    oc_get_sa_before = json.dumps(service_account)
    service_account_after = copy.deepcopy(service_account)
    service_account_after['secrets'].append(new_secret)
    oc_get_sa_after = json.dumps(service_account_after)

    builder['secrets'].append(new_secret)

    mock_cmd = mocker.patch('oc_serviceaccount_secret.OCServiceAccountSecret._run',
                            side_effect=[
                                (0, oc_get_sa_before, ''),  # First call to the mock
                                (0, oc_get_sa_before, ''),  # Second call to the mock
                                (0, 'serviceaccount "builder" replaced', ''),  # Third call to the mock
                                (0, oc_get_sa_after, ''),  # Fourth call to the mock
                            ])

    # Act
    results = oc_serviceaccount_secret.OCServiceAccountSecret.run_ansible(params, False)

    # Assert
    assert results['changed'] is True
    assert results['results']['returncode'] == 0
    assert results['state'] == 'present'

    # Making sure our mocks were called as we expected
    mock_cmd.assert_has_calls([
        mock.call(['oc', 'get', 'sa', 'builder', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'get', 'sa', 'builder', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'replace', '-f', mock.ANY, '-n', 'default'], None),
        mock.call(['oc', 'get', 'sa', 'builder', '-o', 'json', '-n', 'default'], None)
    ])

    # assert_called_once is not available in python 3.5
    assert spy_write.call_count == 1
    assert yaml_provider.safe_load(spy_write.call_args[0][1]) == builder


def test_removing_a_secret_to_a_serviceaccount(yaml_provider, mocker, service_account, builder):
    ''' Testing removing a secret to a service account '''
    mocker.patch('oc_serviceaccount_secret.locate_oc_binary', return_value='oc')
    mocker.patch('oc_serviceaccount_secret.Utils.create_tmpfile_copy', return_value='/tmp/mocked_kubeconfig')
    spy_write = mocker.spy(oc_serviceaccount_secret.Yedit, '_write')

    # Arrange

    # run_ansible input parameters
    params = {
        'state': 'absent',
        'namespace': 'default',
        'secret': 'newsecret',
        'service_account': 'builder',
        'kubeconfig': '/etc/origin/master/admin.kubeconfig',
        'debug': False,
    }

    new_secret = {'name': 'newsecret'}

    service_account_before = copy.deepcopy(service_account)
    service_account_before['secrets'].append(new_secret)
    oc_get_sa_before = json.dumps(service_account_before)

    # Return values of our mocked function call. These get returned once per call.
    mock_cmd = mocker.patch('oc_serviceaccount_secret.OCServiceAccountSecret._run',
                            side_effect=[
                                (0, oc_get_sa_before, ''),  # First call to the mock
                                (0, oc_get_sa_before, ''),  # Second call to the mock
                                (0, 'serviceaccount "builder" replaced', ''),  # Third call to the mock
                            ])

    # Act
    results = oc_serviceaccount_secret.OCServiceAccountSecret.run_ansible(params, False)

    # Assert
    assert results['changed'] is True
    assert results['results']['returncode'] == 0
    assert results['state'] == 'absent'

    # Making sure our mocks were called as we expected
    mock_cmd.assert_has_calls([
        mock.call(['oc', 'get', 'sa', 'builder', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'get', 'sa', 'builder', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'replace', '-f', mock.ANY, '-n', 'default'], None),
    ])

    # assert_called_once is not available in python 3.5
    assert spy_write.call_count == 1
    assert yaml_provider.safe_load(spy_write.call_args[0][1]) == builder


def test_binary_lookup(binary_lookup_test_data, mocker):
    path = binary_lookup_test_data['path']
    which_result = binary_lookup_test_data['which_result']
    binary_expected = binary_lookup_test_data['binary_expected']
    binaries = binary_lookup_test_data['binaries']

    mocker.patch('os.environ.get', side_effect=lambda _v, _d: path)

    if six.PY2:
        mocker.patch('os.path.exists', side_effect=lambda f: f in binaries)
    else:
        mocker.patch('shutil.which', side_effect=lambda _f, path=None: which_result)

    assert oc_serviceaccount_secret.locate_oc_binary() == binary_expected
