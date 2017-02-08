#!/usr/bin/env python2
'''
 Unit tests for oc label
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
from oc_label import OCLabel  # noqa: E402


class OCLabelTest(unittest.TestCase):
    '''
     Test class for OCLabel
    '''

    def setUp(self):
        ''' setup method will create a file and set to known configuration '''
        pass

    @mock.patch('oc_label.Utils.create_tmpfile_copy')
    @mock.patch('oc_label.OCLabel._run')
    def test_state_list(self, mock_cmd, mock_tmpfile_copy):
        ''' Testing a label list '''
        params = {'name': 'default',
                  'namespace': 'default',
                  'labels': None,
                  'state': 'list',
                  'kind': 'namespace',
                  'selector': None,
                  'kubeconfig': '/etc/origin/master/admin.kubeconfig',
                  'debug': False}

        ns = '''{
            "kind": "Namespace",
            "apiVersion": "v1",
            "metadata": {
                "name": "default",
                "selfLink": "/api/v1/namespaces/default",
                "uid": "c45b9547-e3d3-11e6-ba9c-0eece8f2ce22",
                "resourceVersion": "403024",
                "creationTimestamp": "2017-01-26T14:28:55Z",
                "labels": {
                    "storage_pv_quota": "False"
                },
                "annotations": {
                    "openshift.io/node-selector": "",
                    "openshift.io/sa.initialized-roles": "true",
                    "openshift.io/sa.scc.mcs": "s0:c1,c0",
                    "openshift.io/sa.scc.supplemental-groups": "1000000000/10000",
                    "openshift.io/sa.scc.uid-range": "1000000000/10000"
                }
            },
            "spec": {
                "finalizers": [
                    "kubernetes",
                    "openshift.io/origin"
                ]
            },
            "status": {
                "phase": "Active"
            }
        }'''

        mock_cmd.side_effect = [
            (0, ns, ''),
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mocked_kubeconfig',
        ]

        results = OCLabel.run_ansible(params, False)

        self.assertFalse(results['changed'])
        self.assertTrue(results['results']['labels'] == [{'storage_pv_quota': 'False'}])

    @mock.patch('oc_label.Utils.create_tmpfile_copy')
    @mock.patch('oc_label.OCLabel._run')
    def test_state_present(self, mock_cmd, mock_tmpfile_copy):
        ''' Testing a label list '''
        params = {'name': 'default',
                  'namespace': 'default',
                  'labels': [
                      {'key': 'awesomens', 'value': 'testinglabel'},
                      {'key': 'storage_pv_quota', 'value': 'False'}
                  ],
                  'state': 'present',
                  'kind': 'namespace',
                  'selector': None,
                  'kubeconfig': '/etc/origin/master/admin.kubeconfig',
                  'debug': False}

        ns = '''{
            "kind": "Namespace",
            "apiVersion": "v1",
            "metadata": {
                "name": "default",
                "selfLink": "/api/v1/namespaces/default",
                "uid": "c45b9547-e3d3-11e6-ba9c-0eece8f2ce22",
                "resourceVersion": "403024",
                "creationTimestamp": "2017-01-26T14:28:55Z",
                "labels": {
                    "storage_pv_quota": "False"
                },
                "annotations": {
                    "openshift.io/node-selector": "",
                    "openshift.io/sa.initialized-roles": "true",
                    "openshift.io/sa.scc.mcs": "s0:c1,c0",
                    "openshift.io/sa.scc.supplemental-groups": "1000000000/10000",
                    "openshift.io/sa.scc.uid-range": "1000000000/10000"
                }
            },
            "spec": {
                "finalizers": [
                    "kubernetes",
                    "openshift.io/origin"
                ]
            },
            "status": {
                "phase": "Active"
            }
        }'''

        ns1 = '''{
            "kind": "Namespace",
            "apiVersion": "v1",
            "metadata": {
                "name": "default",
                "selfLink": "/api/v1/namespaces/default",
                "uid": "c45b9547-e3d3-11e6-ba9c-0eece8f2ce22",
                "resourceVersion": "403024",
                "creationTimestamp": "2017-01-26T14:28:55Z",
                "labels": {
                    "storage_pv_quota": "False",
                    "awesomens": "testinglabel"
                },
                "annotations": {
                    "openshift.io/node-selector": "",
                    "openshift.io/sa.initialized-roles": "true",
                    "openshift.io/sa.scc.mcs": "s0:c1,c0",
                    "openshift.io/sa.scc.supplemental-groups": "1000000000/10000",
                    "openshift.io/sa.scc.uid-range": "1000000000/10000"
                }
            },
            "spec": {
                "finalizers": [
                    "kubernetes",
                    "openshift.io/origin"
                ]
            },
            "status": {
                "phase": "Active"
            }
        }'''

        mock_cmd.side_effect = [
            (0, ns, ''),
            (0, '', ''),
            (0, ns1, ''),
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mocked_kubeconfig',
        ]

        results = OCLabel.run_ansible(params, False)

        self.assertTrue(results['changed'])
        self.assertTrue(results['results']['results']['labels'][0] ==
                        {'storage_pv_quota': 'False', 'awesomens': 'testinglabel'})

    def tearDown(self):
        '''TearDown method'''
        pass


if __name__ == "__main__":
    unittest.main()
