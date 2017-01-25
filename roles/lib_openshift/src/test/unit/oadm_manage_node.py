#!/usr/bin/env python2
'''
 Unit tests for oadm_manage_node
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
from oadm_manage_node import ManageNode  # noqa: E402


class ManageNodeTest(unittest.TestCase):
    '''
     Test class for oadm_manage_node
    '''

    def setUp(self):
        ''' setup method will create a file and set to known configuration '''
        pass

    @mock.patch('oadm_manage_node.ManageNode.openshift_cmd')
    def test_state_list(self, mock_openshift_cmd):
        ''' Testing a get '''
        params = {'node': 'test-node-1',
                  'namespace': 'default',
                  'selector': None,
                  'pod_selector': None,
                  'list_pods': True,
                  'kubeconfig': '/etc/origin/master/admin.kubeconfig',
                  'evacuate': False,
                  'grace_period': False,
                  'dry_run': False,
                  'force': False}

        dc = '''{"kind": "DeploymentConfig",
               "apiVersion": "v1",
               "metadata": {
                   "name": "router",
                   "namespace": "default",
                   "selfLink": "/oapi/v1/namespaces/default/deploymentconfigs/router",
                   "uid": "a441eedc-e1ae-11e6-a2d5-0e6967f34d42",
                   "resourceVersion": "6558",
                   "generation": 8,
                   "creationTimestamp": "2017-01-23T20:58:07Z",
                   "labels": {
                       "router": "router"
                   }
               },
               "spec": {
                   "replicas": 2,
               }
           }'''

        mock_openshift_cmd.side_effect = [
            {"cmd": '/usr/bin/oc get dc router -n default',
             'results': dc,
             'returncode': 0}]

        results = OCScale.run_ansible(params, False)

        self.assertFalse(results['changed'])
        self.assertEqual(results['result'][0], 2)

    @mock.patch('oc_scale.OCScale.openshift_cmd')
    def test_scale(self, mock_openshift_cmd):
        ''' Testing a get '''
        params = {'name': 'router',
                  'namespace': 'default',
                  'replicas': 3,
                  'state': 'list',
                  'kind': 'dc',
                  'kubeconfig': '/etc/origin/master/admin.kubeconfig',
                  'debug': False}

        dc = '''{"kind": "DeploymentConfig",
               "apiVersion": "v1",
               "metadata": {
                   "name": "router",
                   "namespace": "default",
                   "selfLink": "/oapi/v1/namespaces/default/deploymentconfigs/router",
                   "uid": "a441eedc-e1ae-11e6-a2d5-0e6967f34d42",
                   "resourceVersion": "6558",
                   "generation": 8,
                   "creationTimestamp": "2017-01-23T20:58:07Z",
                   "labels": {
                       "router": "router"
                   }
               },
               "spec": {
                   "replicas": 3,
               }
           }'''

        mock_openshift_cmd.side_effect = [
            {"cmd": '/usr/bin/oc get dc router -n default',
             'results': dc,
             'returncode': 0},
            {"cmd": '/usr/bin/oc create -f /tmp/router -n default',
             'results': '',
             'returncode': 0}
        ]

        results = OCScale.run_ansible(params, False)

        self.assertFalse(results['changed'])
        self.assertEqual(results['result'][0], 3)

    def tearDown(self):
        '''TearDown method'''
        pass


if __name__ == "__main__":
    unittest.main()
