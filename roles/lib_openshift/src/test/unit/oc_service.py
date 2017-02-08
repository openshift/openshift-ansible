#!/usr/bin/env python2
'''
 Unit tests for oc service
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
from oc_service import OCService  # noqa: E402


# pylint: disable=too-many-public-methods
class OCServiceTest(unittest.TestCase):
    '''
     Test class for OCService
    '''

    def setUp(self):
        ''' setup method will create a file and set to known configuration '''
        pass

    @mock.patch('oc_service.Utils.create_tmpfile_copy')
    @mock.patch('oc_service.OCService._run')
    def test_state_list(self, mock_cmd, mock_tmpfile_copy):
        ''' Testing a get '''
        params = {'name': 'router',
                  'namespace': 'default',
                  'ports': None,
                  'state': 'list',
                  'labels': None,
                  'clusterip': None,
                  'portalip': None,
                  'selector': None,
                  'session_affinity': None,
                  'service_type': None,
                  'kubeconfig': '/etc/origin/master/admin.kubeconfig',
                  'debug': False}

        service = '''{
            "kind": "Service",
            "apiVersion": "v1",
            "metadata": {
                "name": "router",
                "namespace": "default",
                "selfLink": "/api/v1/namespaces/default/services/router",
                "uid": "fabd2440-e3d8-11e6-951c-0e3dd518cefa",
                "resourceVersion": "3206",
                "creationTimestamp": "2017-01-26T15:06:14Z",
                "labels": {
                    "router": "router"
                }
            },
            "spec": {
                "ports": [
                    {
                        "name": "80-tcp",
                        "protocol": "TCP",
                        "port": 80,
                        "targetPort": 80
                    },
                    {
                        "name": "443-tcp",
                        "protocol": "TCP",
                        "port": 443,
                        "targetPort": 443
                    },
                    {
                        "name": "1936-tcp",
                        "protocol": "TCP",
                        "port": 1936,
                        "targetPort": 1936
                    },
                    {
                        "name": "5000-tcp",
                        "protocol": "TCP",
                        "port": 5000,
                        "targetPort": 5000
                    }
                ],
                "selector": {
                    "router": "router"
                },
                "clusterIP": "172.30.129.161",
                "type": "ClusterIP",
                "sessionAffinity": "None"
            },
            "status": {
                "loadBalancer": {}
            }
        }'''
        mock_cmd.side_effect = [
            (0, service, '')
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mocked_kubeconfig',
        ]

        results = OCService.run_ansible(params, False)

        self.assertFalse(results['changed'])
        self.assertEqual(results['results']['results'][0]['metadata']['name'], 'router')

    @mock.patch('oc_service.Utils.create_tmpfile_copy')
    @mock.patch('oc_service.OCService._run')
    def test_create(self, mock_cmd, mock_tmpfile_copy):
        ''' Testing a create service '''
        params = {'name': 'router',
                  'namespace': 'default',
                  'ports': {'name': '9000-tcp',
                            'port': 9000,
                            'protocol': 'TCP',
                            'targetPOrt': 9000},
                  'state': 'present',
                  'labels': None,
                  'clusterip': None,
                  'portalip': None,
                  'selector': {'router': 'router'},
                  'session_affinity': 'ClientIP',
                  'service_type': 'ClusterIP',
                  'kubeconfig': '/etc/origin/master/admin.kubeconfig',
                  'debug': False}

        service = '''{
            "kind": "Service",
            "apiVersion": "v1",
            "metadata": {
                "name": "router",
                "namespace": "default",
                "selfLink": "/api/v1/namespaces/default/services/router",
                "uid": "fabd2440-e3d8-11e6-951c-0e3dd518cefa",
                "resourceVersion": "3206",
                "creationTimestamp": "2017-01-26T15:06:14Z",
                "labels": {
                    "router": "router"
                }
            },
            "spec": {
                "ports": [
                    {
                        "name": "80-tcp",
                        "protocol": "TCP",
                        "port": 80,
                        "targetPort": 80
                    },
                    {
                        "name": "443-tcp",
                        "protocol": "TCP",
                        "port": 443,
                        "targetPort": 443
                    },
                    {
                        "name": "1936-tcp",
                        "protocol": "TCP",
                        "port": 1936,
                        "targetPort": 1936
                    },
                    {
                        "name": "5000-tcp",
                        "protocol": "TCP",
                        "port": 5000,
                        "targetPort": 5000
                    }
                ],
                "selector": {
                    "router": "router"
                },
                "clusterIP": "172.30.129.161",
                "type": "ClusterIP",
                "sessionAffinity": "None"
            },
            "status": {
                "loadBalancer": {}
            }
        }'''
        mock_cmd.side_effect = [
            (1, '', 'Error from server: services "router" not found'),
            (1, '', 'Error from server: services "router" not found'),
            (0, service, ''),
            (0, service, '')
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mocked_kubeconfig',
        ]

        results = OCService.run_ansible(params, False)

        self.assertTrue(results['changed'])
        self.assertTrue(results['results']['returncode'] == 0)
        self.assertEqual(results['results']['results'][0]['metadata']['name'], 'router')

    def tearDown(self):
        '''TearDown method'''
        pass


if __name__ == "__main__":
    unittest.main()
