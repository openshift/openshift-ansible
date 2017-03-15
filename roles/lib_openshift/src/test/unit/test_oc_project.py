'''
 Unit tests for oc project
'''
import mock

from lib_openshift.library import oc_project

MODULE_UNDER_TEST = oc_project
CLASS_UNDER_TEST = oc_project.OCProject


def test_adding_a_project(mock_run_cmd):
    ''' Testing adding a project '''

    # Arrange

    # run_ansible input parameters
    params = {
        'state': 'present',
        'display_name': 'operations project',
        'name': 'operations',
        'node_selector': ['ops_only=True'],
        'kubeconfig': '/etc/origin/master/admin.kubeconfig',
        'debug': False,
        'admin': None,
        'admin_role': 'admin',
        'description': 'All things operations project',
    }

    project_results = '''{
        "kind": "Project",
        "apiVersion": "v1",
        "metadata": {
            "name": "operations",
            "selfLink": "/oapi/v1/projects/operations",
            "uid": "5e52afb8-ee33-11e6-89f4-0edc441d9666",
            "resourceVersion": "1584",
            "labels": {},
            "annotations": {
                "openshift.io/node-selector": "ops_only=True",
                "openshift.io/sa.initialized-roles": "true",
                "openshift.io/sa.scc.mcs": "s0:c3,c2",
                "openshift.io/sa.scc.supplemental-groups": "1000010000/10000",
                "openshift.io/sa.scc.uid-range": "1000010000/10000"
            }
        },
        "spec": {
            "finalizers": [
                "kubernetes",
                "openshift.io/origin"
            ]
        },
        "status": {
            "phase": "Active"
        }
    }'''

    # Return values of our mocked function call. These get returned once per call.
    mock_run_cmd.side_effect = [
        (1, '', 'Error from server: namespaces "operations" not found'),
        (1, '', 'Error from server: namespaces "operations" not found'),
        (0, '', ''),  # created
        (0, project_results, ''),  # fetch it
    ]

    # Act

    results = CLASS_UNDER_TEST.run_ansible(params, False)

    # Assert
    assert results['changed'] is True
    assert results['results']['returncode'] == 0
    assert results['results']['results']['metadata']['name'] == 'operations'
    assert results['state'] == 'present'

    # Making sure our mock was called as we expected
    mock_run_cmd.assert_has_calls([
        mock.call(['oc', 'get', 'namespace', 'operations', '-o', 'json'], None),
        mock.call(['oc', 'get', 'namespace', 'operations', '-o', 'json'], None),
        mock.call(['oc', 'adm', 'new-project', 'operations', mock.ANY,
                   mock.ANY, mock.ANY, mock.ANY], None),
        mock.call(['oc', 'get', 'namespace', 'operations', '-o', 'json'], None),

    ])
