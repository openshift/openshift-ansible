#!/usr/bin/env python2
'''
 Unit tests for oc secret add
'''
# To run:
# ./oc_serviceaccount_secret.py
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
from oc_serviceaccount_secret import OCServiceAccountSecret  # noqa: E402


class OCServiceAccountSecretTest(unittest.TestCase):
    '''
     Test class for OCServiceAccountSecret
    '''

    def setUp(self):
        ''' setup method will create a file and set to known configuration '''
        pass

    @mock.patch('oc_serviceaccount_secret.Yedit._write')
    @mock.patch('oc_serviceaccount_secret.OCServiceAccountSecret._run')
    def test_adding_a_secret_to_a_serviceaccount(self, mock_cmd, mock_write):
        ''' Testing adding a secret to a service account '''

        # Arrange

        # run_ansible input parameters
        params = {
            'state': 'present',
            'namespace': 'default',
            'secret': 'newsecret',
            'service_account': 'builder',
            'kubeconfig': '/etc/origin/master/admin.kubeconfig',
            'debug': False,
        }

        oc_get_sa_before = '''{
            "kind": "ServiceAccount",
            "apiVersion": "v1",
            "metadata": {
                "name": "builder",
                "namespace": "default",
                "selfLink": "/api/v1/namespaces/default/serviceaccounts/builder",
                "uid": "cf47bca7-ebc4-11e6-b041-0ed9df7abc38",
                "resourceVersion": "302879",
                "creationTimestamp": "2017-02-05T17:02:00Z"
            },
            "secrets": [
                {
                    "name": "builder-dockercfg-rsrua"
                },
                {
                    "name": "builder-token-akqxi"
                }

            ],
            "imagePullSecrets": [
                {
                    "name": "builder-dockercfg-rsrua"
                }
            ]
        }
        '''

        oc_get_sa_after = '''{
            "kind": "ServiceAccount",
            "apiVersion": "v1",
            "metadata": {
                "name": "builder",
                "namespace": "default",
                "selfLink": "/api/v1/namespaces/default/serviceaccounts/builder",
                "uid": "cf47bca7-ebc4-11e6-b041-0ed9df7abc38",
                "resourceVersion": "302879",
                "creationTimestamp": "2017-02-05T17:02:00Z"
            },
            "secrets": [
                {
                    "name": "builder-dockercfg-rsrua"
                },
                {
                    "name": "builder-token-akqxi"
                },
                {
                    "name": "newsecret"
                }

            ],
            "imagePullSecrets": [
                {
                    "name": "builder-dockercfg-rsrua"
                }
            ]
        }
        '''

        builder_yaml_file = '''\
secrets:
- name: builder-dockercfg-rsrua
- name: builder-token-akqxi
- name: newsecret
kind: ServiceAccount
imagePullSecrets:
- name: builder-dockercfg-rsrua
apiVersion: v1
metadata:
  name: builder
  namespace: default
  resourceVersion: '302879'
  creationTimestamp: '2017-02-05T17:02:00Z'
  selfLink: /api/v1/namespaces/default/serviceaccounts/builder
  uid: cf47bca7-ebc4-11e6-b041-0ed9df7abc38
'''

        # Return values of our mocked function call. These get returned once per call.
        mock_cmd.side_effect = [
            (0, oc_get_sa_before, ''),  # First call to the mock
            (0, oc_get_sa_before, ''),  # Second call to the mock
            (0, 'serviceaccount "builder" replaced', ''),  # Third call to the mock
            (0, oc_get_sa_after, ''),  # Fourth call to the mock
        ]

        # Act
        results = OCServiceAccountSecret.run_ansible(params, False)

        # Assert
        self.assertTrue(results['changed'])
        self.assertEqual(results['results']['returncode'], 0)
        self.assertEqual(results['state'], 'present')

        # Making sure our mocks were called as we expected
        mock_cmd.assert_has_calls([
            mock.call(['oc', '-n', 'default', 'get', 'sa', 'builder', '-o', 'json'], None),
            mock.call(['oc', '-n', 'default', 'get', 'sa', 'builder', '-o', 'json'], None),
            mock.call(['oc', '-n', 'default', 'replace', '-f', '/tmp/builder'], None),
            mock.call(['oc', '-n', 'default', 'get', 'sa', 'builder', '-o', 'json'], None)
        ])

        mock_write.assert_has_calls([
            mock.call('/tmp/builder', builder_yaml_file)
        ])

    @mock.patch('oc_serviceaccount_secret.Yedit._write')
    @mock.patch('oc_serviceaccount_secret.OCServiceAccountSecret._run')
    def test_removing_a_secret_to_a_serviceaccount(self, mock_cmd, mock_write):
        ''' Testing adding a secret to a service account '''

        # Arrange

        # run_ansible input parameters
        params = {
            'state': 'absent',
            'namespace': 'default',
            'secret': 'newsecret',
            'service_account': 'builder',
            'kubeconfig': '/etc/origin/master/admin.kubeconfig',
            'debug': False,
        }

        oc_get_sa_before = '''{
            "kind": "ServiceAccount",
            "apiVersion": "v1",
            "metadata": {
                "name": "builder",
                "namespace": "default",
                "selfLink": "/api/v1/namespaces/default/serviceaccounts/builder",
                "uid": "cf47bca7-ebc4-11e6-b041-0ed9df7abc38",
                "resourceVersion": "302879",
                "creationTimestamp": "2017-02-05T17:02:00Z"
            },
            "secrets": [
                {
                    "name": "builder-dockercfg-rsrua"
                },
                {
                    "name": "builder-token-akqxi"
                },
                {
                    "name": "newsecret"
                }

            ],
            "imagePullSecrets": [
                {
                    "name": "builder-dockercfg-rsrua"
                }
            ]
        }
        '''

        builder_yaml_file = '''\
secrets:
- name: builder-dockercfg-rsrua
- name: builder-token-akqxi
kind: ServiceAccount
imagePullSecrets:
- name: builder-dockercfg-rsrua
apiVersion: v1
metadata:
  name: builder
  namespace: default
  resourceVersion: '302879'
  creationTimestamp: '2017-02-05T17:02:00Z'
  selfLink: /api/v1/namespaces/default/serviceaccounts/builder
  uid: cf47bca7-ebc4-11e6-b041-0ed9df7abc38
'''

        # Return values of our mocked function call. These get returned once per call.
        mock_cmd.side_effect = [
            (0, oc_get_sa_before, ''),  # First call to the mock
            (0, oc_get_sa_before, ''),  # Second call to the mock
            (0, 'serviceaccount "builder" replaced', ''),  # Third call to the mock
        ]

        # Act
        results = OCServiceAccountSecret.run_ansible(params, False)

        # Assert
        self.assertTrue(results['changed'])
        self.assertEqual(results['results']['returncode'], 0)
        self.assertEqual(results['state'], 'absent')

        # Making sure our mocks were called as we expected
        mock_cmd.assert_has_calls([
            mock.call(['oc', '-n', 'default', 'get', 'sa', 'builder', '-o', 'json'], None),
            mock.call(['oc', '-n', 'default', 'get', 'sa', 'builder', '-o', 'json'], None),
            mock.call(['oc', '-n', 'default', 'replace', '-f', '/tmp/builder'], None),
        ])

        mock_write.assert_has_calls([
            mock.call('/tmp/builder', builder_yaml_file)
        ])

    def tearDown(self):
        '''TearDown method'''
        pass


if __name__ == "__main__":
    unittest.main()
