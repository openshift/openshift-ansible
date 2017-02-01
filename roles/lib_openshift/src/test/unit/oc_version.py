#!/usr/bin/env python2
'''
 Unit tests for oc version
'''
# To run
# python -m unittest version
#
# .
# Ran 1 test in 0.597s
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
from oc_version import OCVersion  # noqa: E402


class OCVersionTest(unittest.TestCase):
    '''
     Test class for OCVersion
    '''

    def setUp(self):
        ''' setup method will create a file and set to known configuration '''
        pass

    @mock.patch('oc_version.OCVersion.openshift_cmd')
    def test_get(self, mock_openshift_cmd):
        ''' Testing a get '''
        params = {'kubeconfig': '/etc/origin/master/admin.kubeconfig',
                  'state': 'list',
                  'debug': False}

        mock_openshift_cmd.side_effect = [
            {"cmd": "oc version",
             "results": "oc v3.4.0.39\nkubernetes v1.4.0+776c994\n" +
                        "features: Basic-Auth GSSAPI Kerberos SPNEGO\n\n" +
                        "Server https://internal.api.opstest.openshift.com" +
                        "openshift v3.4.0.39\n" +
                        "kubernetes v1.4.0+776c994\n",
             "returncode": 0}
        ]

        results = OCVersion.run_ansible(params)

        self.assertFalse(results['changed'])
        self.assertEqual(results['results']['oc_short'], '3.4')
        self.assertEqual(results['results']['oc_numeric'], '3.4.0.39')
        self.assertEqual(results['results']['kubernetes_numeric'], '1.4.0')

    def tearDown(self):
        '''TearDown method'''
        pass


if __name__ == "__main__":
    unittest.main()
