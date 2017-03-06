'''
 Unit tests for oc secret add
'''
import copy
import json
import mock

import pytest

from lib_openshift.library import oc_serviceaccount_secret

MODULE_UNDER_TEST = oc_serviceaccount_secret
CLASS_UNDER_TEST = oc_serviceaccount_secret.OCServiceAccountSecret


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


def test_adding_a_secret_to_a_serviceaccount(mocker, yaml_provider, mock_run_cmd, service_account, builder):
    ''' Testing adding a secret to a service account '''
    # Arrange
    spy_write = mocker.spy(oc_serviceaccount_secret.Yedit, '_write')

    new_secret = {'name': 'newsecret'}

    oc_get_sa_before = json.dumps(service_account)
    service_account_after = copy.deepcopy(service_account)
    service_account_after['secrets'].append(new_secret)
    oc_get_sa_after = json.dumps(service_account_after)

    builder['secrets'].append(new_secret)

    mock_run_cmd.side_effect = [
        (0, oc_get_sa_before, ''),  # First call to the mock
        (0, oc_get_sa_before, ''),  # Second call to the mock
        (0, 'serviceaccount "builder" replaced', ''),  # Third call to the mock
        (0, oc_get_sa_after, ''),  # Fourth call to the mock
    ]

    # run_ansible input parameters
    params = {
        'state': 'present',
        'namespace': 'default',
        'secret': 'newsecret',
        'service_account': 'builder',
        'kubeconfig': '/etc/origin/master/admin.kubeconfig',
        'debug': False,
    }

    # Act
    results = CLASS_UNDER_TEST.run_ansible(params, False)

    # Assert
    assert results['changed'] is True
    assert results['results']['returncode'] == 0
    assert results['state'] == 'present'

    # Making sure our mocks were called as we expected
    mock_run_cmd.assert_has_calls([
        mock.call(['oc', 'get', 'sa', 'builder', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'get', 'sa', 'builder', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'replace', '-f', mock.ANY, '-n', 'default'], None),
        mock.call(['oc', 'get', 'sa', 'builder', '-o', 'json', '-n', 'default'], None)
    ])

    # assert_called_once is not available in python 3.5
    assert spy_write.call_count == 1
    assert yaml_provider.safe_load(spy_write.call_args[0][1]) == builder


def test_removing_a_secret_to_a_serviceaccount(yaml_provider, mocker, mock_run_cmd, service_account, builder):
    ''' Testing removing a secret to a service account '''
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
    mock_run_cmd.side_effect = [
        (0, oc_get_sa_before, ''),  # First call to the mock
        (0, oc_get_sa_before, ''),  # Second call to the mock
        (0, 'serviceaccount "builder" replaced', ''),  # Third call to the mock
    ]

    # Act
    results = CLASS_UNDER_TEST.run_ansible(params, False)

    # Assert
    assert results['changed'] is True
    assert results['results']['returncode'] == 0
    assert results['state'] == 'absent'

    # Making sure our mocks were called as we expected
    mock_run_cmd.assert_has_calls([
        mock.call(['oc', 'get', 'sa', 'builder', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'get', 'sa', 'builder', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'replace', '-f', mock.ANY, '-n', 'default'], None),
    ])

    # assert_called_once is not available in python 3.5
    assert spy_write.call_count == 1
    assert yaml_provider.safe_load(spy_write.call_args[0][1]) == builder
