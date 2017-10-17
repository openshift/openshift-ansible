'''
 Unit tests for oc serviceaccount
'''

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
from oc_storageclass import OCStorageClass  # noqa: E402


class OCStorageClassTest(unittest.TestCase):
    '''
     Test class for OCStorageClass
    '''
    params = {'kubeconfig': '/etc/origin/master/admin.kubeconfig',
              'state': 'present',
              'debug': False,
              'name': 'testsc',
              'provisioner': 'kubernetes.io/aws-ebs',
              'annotations': {'storageclass.beta.kubernetes.io/is-default-class': "true"},
              'parameters': {'type': 'gp2'},
              'api_version': 'v1',
              'default_storage_class': 'true'}

    @mock.patch('oc_storageclass.locate_oc_binary')
    @mock.patch('oc_storageclass.Utils.create_tmpfile_copy')
    @mock.patch('oc_storageclass.OCStorageClass._run')
    def test_adding_a_storageclass(self, mock_cmd, mock_tmpfile_copy, mock_oc_binary):
        ''' Testing adding a storageclass '''

        # Arrange

        # run_ansible input parameters

        valid_result_json = '''{
            "kind": "StorageClass",
            "apiVersion": "v1",
            "metadata": {
                "name": "testsc",
                "selfLink": "/apis/storage.k8s.io/v1/storageclasses/gp2",
                "uid": "4d8320c9-e66f-11e6-8edc-0eece8f2ce22",
                "resourceVersion": "2828",
                "creationTimestamp": "2017-01-29T22:07:19Z",
                "annotations": {"storageclass.beta.kubernetes.io/is-default-class": "true"}
            },
            "provisioner": "kubernetes.io/aws-ebs",
            "parameters": {"type": "gp2"}
        }'''

        # Return values of our mocked function call. These get returned once per call.
        mock_cmd.side_effect = [
            # First call to mock
            (1, '', 'Error from server: storageclass "testsc" not found'),

            # Second call to mock
            (0, 'storageclass "testsc" created', ''),

            # Third call to mock
            (0, valid_result_json, ''),
        ]

        mock_oc_binary.side_effect = [
            'oc'
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mocked_kubeconfig',
        ]

        # Act
        results = OCStorageClass.run_ansible(OCStorageClassTest.params, False)

        # Assert
        self.assertTrue(results['changed'])
        self.assertEqual(results['results']['returncode'], 0)
        self.assertEqual(results['state'], 'present')

        # Making sure our mock was called as we expected
        mock_cmd.assert_has_calls([
            mock.call(['oc', 'get', 'storageclass', 'testsc', '-o', 'json'], None),
            mock.call(['oc', 'create', '-f', mock.ANY], None),
            mock.call(['oc', 'get', 'storageclass', 'testsc', '-o', 'json'], None),
        ])
