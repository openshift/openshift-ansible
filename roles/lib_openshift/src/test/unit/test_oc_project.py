'''
 Unit tests for oc project
'''

import os
import sys
import unittest
import mock

# Removing invalid variable names for tests so that I can
# keep them brief
# pylint: disable=invalid-name,no-name-in-module
# Disable import-error b/c our libraries aren't loaded in jenkins
# pylint: disable=import-error,wrong-import-position
# place class in our python path
module_path = os.path.join('/'.join(os.path.realpath(__file__).split('/')[:-4]), 'library')  # noqa: E501
sys.path.insert(0, module_path)
from oc_project import OCProject  # noqa: E402


class OCProjectTest(unittest.TestCase):
    '''
     Test class for OCSecret
    '''

    @mock.patch('oc_project.locate_oc_binary')
    @mock.patch('oc_project.Utils.create_tmpfile_copy')
    @mock.patch('oc_project.Utils._write')
    @mock.patch('oc_project.OCProject._run')
    def test_adding_a_project(self, mock_cmd, mock_write, mock_tmpfile_copy, mock_loc_oc_bin):
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
        mock_cmd.side_effect = [
            (1, '', 'Error from server: namespaces "operations" not found'),
            (1, '', 'Error from server: namespaces "operations" not found'),
            (0, '', ''),  # created
            (0, project_results, ''),  # fetch it
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mocked_kubeconfig',
        ]

        mock_loc_oc_bin.side_effect = [
            'oc',
        ]

        # Act

        results = OCProject.run_ansible(params, False)

        # Assert
        self.assertTrue(results['changed'])
        self.assertEqual(results['results']['returncode'], 0)
        self.assertEqual(results['results']['results']['metadata']['name'], 'operations')
        self.assertEqual(results['state'], 'present')

        # Making sure our mock was called as we expected
        mock_cmd.assert_has_calls([
            mock.call(['oc', 'get', 'namespace', 'operations', '-o', 'json'], None),
            mock.call(['oc', 'get', 'namespace', 'operations', '-o', 'json'], None),
            mock.call(['oc', 'adm', 'new-project', 'operations', mock.ANY,
                       mock.ANY, mock.ANY, mock.ANY], None),
            mock.call(['oc', 'get', 'namespace', 'operations', '-o', 'json'], None),

        ])
