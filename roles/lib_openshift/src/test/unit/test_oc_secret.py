'''
 Unit tests for oc secret
'''
import mock

from lib_openshift.library import oc_secret

MODULE_UNDER_TEST = oc_secret
CLASS_UNDER_TEST = oc_secret.OCSecret


def test_adding_a_secret(mocker, mock_run_cmd):
    ''' Testing adding a secret '''

    # Arrange
    mock_write = mocker.patch(MODULE_UNDER_TEST.__name__ + '.Utils._write')

    # run_ansible input parameters
    params = {
        'state': 'present',
        'namespace': 'default',
        'name': 'testsecretname',
        'contents': [{
            'path': "/tmp/somesecret.json",
            'data': "{'one': 1, 'two': 2, 'three': 3}",
        }],
        'decode': False,
        'kubeconfig': '/etc/origin/master/admin.kubeconfig',
        'debug': False,
        'files': None,
        'delete_after': True,
    }

    # Return values of our mocked function call. These get returned once per call.
    mock_run_cmd.side_effect = [
        (1, '', 'Error from server: secrets "testsecretname" not found'),
        (0, 'secret/testsecretname', ''),
    ]

    # Act
    results = CLASS_UNDER_TEST.run_ansible(params, False)

    # Assert
    assert results['changed']
    assert results['results']['returncode'] == 0
    assert results['state'] == 'present'

    # Making sure our mock was called as we expected
    mock_run_cmd.assert_has_calls([
        mock.call(['oc', 'get', 'secrets', 'testsecretname', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'secrets', 'new', 'testsecretname', mock.ANY, '-n', 'default'], None),
    ])

    mock_write.assert_has_calls([
        mock.call(mock.ANY, "{'one': 1, 'two': 2, 'three': 3}"),
    ])
