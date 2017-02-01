#!/usr/bin/env python2
'''
 Unit tests for oc secret
'''
# To run:
# ./oc_secret.py
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
from oc_secret import OCSecret  # noqa: E402


class OCSecretTest(unittest.TestCase):
    '''
     Test class for OCSecret
    '''

    def setUp(self):
        ''' setup method will create a file and set to known configuration '''
        pass

    @mock.patch('oc_secret.OCSecret.openshift_cmd')
    def test_adding_a_secret(self, mock_openshift_cmd):
        ''' Testing adding a secret '''

        # Arrange

        # run_ansible input parameters
        params = {
            'state': 'present',
            'namespace': 'default',
            'name': 'secretname',
            'contents': [{
                'path': "/tmp/somesecret.json",
                'data': "{'one': 1, 'two': 2, 'three', 3}",
            }],
            'decode': False,
            'kubeconfig': '/etc/origin/master/admin.kubeconfig',
            'debug': False,
            'files': None,
            'delete_after': True,
        }

        # Return values of our mocked function call. These get returned once per call.
        mock_openshift_cmd.side_effect = [
            {
                "cmd": "/usr/bin/oc get secrets -o json secretname",
                "results": "",
                "returncode": 0,
            },  # oc output for first call to openshift_cmd (oc secrets get)
            {
                "cmd": "/usr/bin/oc secrets new secretname somesecret.json=/tmp/somesecret.json",
                "results": "",
                "returncode": 0,
            },  # oc output for second call to openshift_cmd (oc secrets new)
        ]

        # Act
        results = OCSecret.run_ansible(params, False)

        # Assert
        self.assertTrue(results['changed'])
        self.assertEqual(results['results']['returncode'], 0)
        self.assertEqual(results['state'], 'present')

        # Making sure our mock was called as we expected
        mock_openshift_cmd.assert_has_calls([
            mock.call(['get', 'secrets', 'secretname', '-o', 'json'], output=True),
            mock.call(['secrets', 'new', 'secretname', 'somesecret.json=/tmp/somesecret.json']),
        ])

    def tearDown(self):
        '''TearDown method'''
        pass


if __name__ == "__main__":
    unittest.main()
