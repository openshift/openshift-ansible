#!/usr/bin/env python2
'''
 Unit tests for oadm certificate authority
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
# pylint: disable=import-error
# place class in our python path
module_path = os.path.join('/'.join(os.path.realpath(__file__).split('/')[:-4]), 'library')  # noqa: E501
sys.path.insert(0, module_path)
from oadm_ca import CertificateAuthority  # noqa: E402


# pylint: disable=too-many-public-methods
class OadmCATest(unittest.TestCase):
    '''
     Test class for oadm_ca
    '''

    def setUp(self):
        ''' setup method will set to known configuration '''
        pass

    @mock.patch('oadm_ca.Utils.create_tmpfile_copy')
    @mock.patch('oadm_ca.CertificateAuthority._run')
    def test_state_list(self, mock_cmd, mock_tmpfile_copy):
        ''' Testing a get '''



        params = {'cmd': 'create-server-cert',
                  'signer_cert': '/etc/origin/master/ca.crt',
                  'signer_key': '/etc/origin/master/ca.key',
                  'signer_serial': '/etc/origin/master/ca.serial.txt',
                  'hostnames': ['registry.test.openshift.com',
                                '127.0.0.1',
                                'docker-registry.default.svc.cluster.local'],
                  'cert': '/etc/origin/master/registry.crt',
                  'key': '/etc/origin/master/registry.key',
                  'kubeconfig': '/etc/origin/master/admin.kubeconfig',
		  'private_key': None,
                  'public_key': None,
                  'cert_dir': None,
                  'master': None,
                  'public_master': None,
                  'overwrite': False,
                  'state': 'present',
                  'debug': False}

        mock_cmd.side_effect = [
            (0, '', '')
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mock_kubeconfig',
        ]

        results = CertificateAuthority.run_ansible(params, False)
        import pdb; pdb.set_trace()

        self.assertFalse(results['changed'])
        self.assertEqual(results['results']['results'][0]['metadata']['name'], 'mysql-ephemeral')

    def tearDown(self):
        '''TearDown method'''
        pass


if __name__ == "__main__":
    unittest.main()
