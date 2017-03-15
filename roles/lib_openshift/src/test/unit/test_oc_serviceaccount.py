'''
 Unit tests for oc serviceaccount
'''
import mock

from lib_openshift.library import oc_serviceaccount

MODULE_UNDER_TEST = oc_serviceaccount
CLASS_UNDER_TEST = oc_serviceaccount.OCServiceAccount


def test_adding_a_serviceaccount(mock_run_cmd):
    ''' Testing adding a serviceaccount '''

    # Arrange

    # run_ansible input parameters
    params = {
        'kubeconfig': '/etc/origin/master/admin.kubeconfig',
        'state': 'present',
        'debug': False,
        'name': 'testserviceaccountname',
        'namespace': 'default',
        'secrets': None,
        'image_pull_secrets': None,
    }

    valid_result_json = '''{
        "kind": "ServiceAccount",
        "apiVersion": "v1",
        "metadata": {
            "name": "testserviceaccountname",
            "namespace": "default",
            "selfLink": "/api/v1/namespaces/default/serviceaccounts/testserviceaccountname",
            "uid": "4d8320c9-e66f-11e6-8edc-0eece8f2ce22",
            "resourceVersion": "328450",
            "creationTimestamp": "2017-01-29T22:07:19Z"
        },
        "secrets": [
            {
                "name": "testserviceaccountname-dockercfg-4lqd0"
            },
            {
                "name": "testserviceaccountname-token-9h0ej"
            }
        ],
        "imagePullSecrets": [
            {
                "name": "testserviceaccountname-dockercfg-4lqd0"
            }
        ]
    }'''

    # Return values of our mocked function call. These get returned once per call.
    mock_run_cmd.side_effect = [
        # First call to mock
        (1, '', 'Error from server: serviceaccounts "testserviceaccountname" not found'),

        # Second call to mock
        (0, 'serviceaccount "testserviceaccountname" created', ''),

        # Third call to mock
        (0, valid_result_json, ''),
    ]

    # Act
    results = CLASS_UNDER_TEST.run_ansible(params, False)

    # Assert
    assert results['changed'] is True
    assert results['results']['returncode'] == 0
    assert results['state'] == 'present'

    # Making sure our mock was called as we expected
    mock_run_cmd.assert_has_calls([
        mock.call(['oc', 'get', 'sa', 'testserviceaccountname', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'create', '-f', mock.ANY, '-n', 'default'], None),
        mock.call(['oc', 'get', 'sa', 'testserviceaccountname', '-o', 'json', '-n', 'default'], None),
    ])
