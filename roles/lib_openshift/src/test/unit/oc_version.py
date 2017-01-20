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

# Removing invalid variable names for tests so that I can
# keep them brief
# pylint: disable=invalid-name,no-name-in-module
# Disable import-error b/c our libraries aren't loaded in jenkins
# pylint: disable=import-error,wrong-import-position
# place class in our python path
module_path = os.path.join('/'.join(os.path.realpath(__file__).split('/')[:-4]), 'library')  # noqa: E501
sys.path.insert(0, module_path)
from oc_version import OCVersion  # noqa: E402


# pylint: disable=unused-argument
def oc_cmd_mock(cmd, oadm=False, output=False, output_type='json', input_data=None):
    '''mock command for openshift_cmd'''
    version = '''oc v3.4.0.39
kubernetes v1.4.0+776c994
features: Basic-Auth GSSAPI Kerberos SPNEGO

Server https://internal.api.opstest.openshift.com
openshift v3.4.0.39
kubernetes v1.4.0+776c994
'''
    if 'version' in cmd:
        return {'stderr': None,
                'stdout': version,
                'returncode': 0,
                'results': version,
                'cmd': cmd}


class OCVersionTest(unittest.TestCase):
    '''
     Test class for OCVersion
    '''

    def setUp(self):
        ''' setup method will create a file and set to known configuration '''
        self.oc_ver = OCVersion(None, False)
        self.oc_ver.openshift_cmd = oc_cmd_mock

    def test_get(self):
        ''' Testing a get '''
        results = self.oc_ver.get()
        self.assertEqual(results['oc_short'], '3.4')
        self.assertEqual(results['oc_numeric'], '3.4.0.39')
        self.assertEqual(results['kubernetes_numeric'], '1.4.0')

    def tearDown(self):
        '''TearDown method'''
        pass


if __name__ == "__main__":
    unittest.main()
