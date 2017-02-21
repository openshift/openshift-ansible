#!/usr/bin/env python2
'''
 Unit tests for oc route
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
from oc_route import OCRoute  # noqa: E402


class OCRouteTest(unittest.TestCase):
    '''
     Test class for OCServiceAccount
    '''

    def setUp(self):
        ''' setup method will create a file and set to known configuration '''
        pass

    @mock.patch('oc_route.Utils.create_tmpfile_copy')
    @mock.patch('oc_route.OCRoute._run')
    def test_list_route(self, mock_cmd, mock_tmpfile_copy):
        ''' Testing getting a route '''

        # Arrange

        # run_ansible input parameters
        params = {
            'kubeconfig': '/etc/origin/master/admin.kubeconfig',
            'state': 'list',
            'debug': False,
            'name': 'test',
            'namespace': 'default',
            'tls_termination': 'passthrough',
            'dest_cacert_path': None,
            'cacert_path': None,
            'cert_path': None,
            'key_path': None,
            'dest_cacert_content': None,
            'cacert_content': None,
            'cert_content': None,
            'key_content': None,
            'service_name': 'testservice',
            'host': 'test.openshift.com',
            'wildcard_policy': None,
            'weight': None,
            'port': None
        }

        route_result = '''{
            "kind": "Route",
            "apiVersion": "v1",
            "metadata": {
                "name": "test",
                "namespace": "default",
                "selfLink": "/oapi/v1/namespaces/default/routes/test",
                "uid": "1b127c67-ecd9-11e6-96eb-0e0d9bdacd26",
                "resourceVersion": "439182",
                "creationTimestamp": "2017-02-07T01:59:48Z"
            },
            "spec": {
                "host": "test.example",
                "to": {
                    "kind": "Service",
                    "name": "test",
                    "weight": 100
                },
                "port": {
                    "targetPort": 8443
                },
                "tls": {
                    "termination": "passthrough"
                },
                "wildcardPolicy": "None"
            },
            "status": {
                "ingress": [
                    {
                        "host": "test.example",
                        "routerName": "router",
                        "conditions": [
                            {
                                "type": "Admitted",
                                "status": "True",
                                "lastTransitionTime": "2017-02-07T01:59:48Z"
                            }
                        ],
                        "wildcardPolicy": "None"
                    }
                ]
            }
        }'''

        # Return values of our mocked function call. These get returned once per call.
        mock_cmd.side_effect = [
            # First call to mock
            (0, route_result, ''),
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mock.kubeconfig',
        ]

        # Act
        results = OCRoute.run_ansible(params, False)

        # Assert
        self.assertFalse(results['changed'])
        self.assertEqual(results['state'], 'list')
        self.assertEqual(results['results'][0]['metadata']['name'], 'test')

        # Making sure our mock was called as we expected
        mock_cmd.assert_has_calls([
            mock.call(['oc', '-n', 'default', 'get', 'route', 'test', '-o', 'json'], None),
        ])

    @mock.patch('oc_route.Utils.create_tmpfile_copy')
    @mock.patch('oc_route.Yedit._write')
    @mock.patch('oc_route.OCRoute._run')
    def test_create_route(self, mock_cmd, mock_write, mock_tmpfile_copy):
        ''' Testing getting a route '''
        # Arrange

        # run_ansible input parameters
        params = {
            'kubeconfig': '/etc/origin/master/admin.kubeconfig',
            'state': 'present',
            'debug': False,
            'name': 'test',
            'namespace': 'default',
            'tls_termination': 'edge',
            'dest_cacert_path': None,
            'cacert_path': None,
            'cert_path': None,
            'key_path': None,
            'dest_cacert_content': None,
            'cacert_content': 'testing',
            'cert_content': 'testing',
            'key_content': 'testing',
            'service_name': 'testservice',
            'host': 'test.openshift.com',
            'wildcard_policy': None,
            'weight': None,
            'port': None
        }

        route_result = '''{
                "apiVersion": "v1",
                "kind": "Route",
                "metadata": {
                    "creationTimestamp": "2017-02-07T20:55:10Z",
                    "name": "test",
                    "namespace": "default",
                    "resourceVersion": "517745",
                    "selfLink": "/oapi/v1/namespaces/default/routes/test",
                    "uid": "b6f25898-ed77-11e6-9755-0e737db1e63a"
                },
                "spec": {
                    "host": "test.openshift.com",
                    "tls": {
                        "caCertificate": "testing",
                        "certificate": "testing",
                        "key": "testing",
                        "termination": "edge"
                    },
                    "to": {
                        "kind": "Service",
                        "name": "testservice",
                        "weight": 100
                    },
                    "wildcardPolicy": "None"
                },
                "status": {
                    "ingress": [
                        {
                            "conditions": [
                                {
                                    "lastTransitionTime": "2017-02-07T20:55:10Z",
                                    "status": "True",
                                    "type": "Admitted"
                                }
                            ],
                            "host": "test.openshift.com",
                            "routerName": "router",
                            "wildcardPolicy": "None"
                        }
                    ]
                }
            }'''

        test_route = '''\
kind: Route
spec:
  tls:
    caCertificate: testing
    termination: edge
    certificate: testing
    key: testing
  to:
    kind: Service
    name: testservice
    weight: 100
  host: test.openshift.com
  wildcardPolicy: None
apiVersion: v1
metadata:
  namespace: default
  name: test
'''

        # Return values of our mocked function call. These get returned once per call.
        mock_cmd.side_effect = [
            # First call to mock
            (1, '', 'Error from server: routes "test" not found'),
            (1, '', 'Error from server: routes "test" not found'),
            (0, 'route "test" created', ''),
            (0, route_result, ''),
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mock.kubeconfig',
        ]

        mock_write.assert_has_calls = [
            # First call to mock
            mock.call('/tmp/test', test_route)
        ]

        # Act
        results = OCRoute.run_ansible(params, False)

        # Assert
        self.assertTrue(results['changed'])
        self.assertEqual(results['state'], 'present')
        self.assertEqual(results['results']['results'][0]['metadata']['name'], 'test')

        # Making sure our mock was called as we expected
        mock_cmd.assert_has_calls([
            mock.call(['oc', '-n', 'default', 'get', 'route', 'test', '-o', 'json'], None),
            mock.call(['oc', '-n', 'default', 'create', '-f', mock.ANY], None),
            mock.call(['oc', '-n', 'default', 'get', 'route', 'test', '-o', 'json'], None),
        ])

    def tearDown(self):
        '''TearDown method'''
        pass


if __name__ == "__main__":
    unittest.main()
