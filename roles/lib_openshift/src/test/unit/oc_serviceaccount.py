#!/usr/bin/env python2
'''
 Unit tests for oc serviceaccount
'''
# To run:
# ./oc_serviceaccount.py
#
# .
# Ran 1 test in 0.002s
#
# OK

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
from oc_serviceaccount import OCServiceAccount  # noqa: E402


class OCServiceAccountTest(unittest.TestCase):
    '''
     Test class for OCServiceAccount
    '''

    def setUp(self):
        ''' setup method will create a file and set to known configuration '''
        pass

    @mock.patch('oc_serviceaccount.OCServiceAccount._run')
    def test_adding_a_serviceaccount(self, mock_cmd):
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
        mock_cmd.side_effect = [
            # First call to mock
            (1, '', 'Error from server: serviceaccounts "testserviceaccountname" not found'),

            # Second call to mock
            (0, 'serviceaccount "testserviceaccountname" created', ''),

            # Third call to mock
            (0, valid_result_json, ''),
        ]

        # Act
        results = OCServiceAccount.run_ansible(params, False)

        # Assert
        self.assertTrue(results['changed'])
        self.assertEqual(results['results']['returncode'], 0)
        self.assertEqual(results['state'], 'present')

        # Making sure our mock was called as we expected
        mock_cmd.assert_has_calls([
            mock.call(['oc', '-n', 'default', 'get', 'sa', 'testserviceaccountname', '-o', 'json'], None),
            mock.call(['oc', '-n', 'default', 'create', '-f', mock.ANY], None),
            mock.call(['oc', '-n', 'default', 'get', 'sa', 'testserviceaccountname', '-o', 'json'], None),
        ])

    def tearDown(self):
        '''TearDown method'''
        pass


if __name__ == "__main__":
    unittest.main()
