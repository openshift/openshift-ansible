#!/usr/bin/env python2
'''
 Unit tests for oc label
'''
# To run
# python -m unittest image
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
from oc_image import OCImage  # noqa: E402


class OCImageTest(unittest.TestCase):
    '''
     Test class for OCImage
    '''

    def setUp(self):
        ''' setup method will create a file and set to known configuration '''
        pass

    @mock.patch('oc_image.Utils.create_tmpfile_copy')
    @mock.patch('oc_image.OCImage._run')
    def test_state_list(self, mock_cmd, mock_tmpfile_copy):
        ''' Testing a image list '''
        params = {'registry_url': 'registry.ops.openshift.com',
                  'image_name': 'oso-rhel7-zagg-web',
                  'image_tag': 'int',
                  'name': 'default',
                  'namespace': 'default',
                  'labels': None,
                  'state': 'list',
                  'kind': 'namespace',
                  'selector': None,
                  'kubeconfig': '/etc/origin/master/admin.kubeconfig',
                  'debug': False}


        istream = '''{
            "kind": "ImageStream",
            "apiVersion": "v1",
            "metadata": {
                "name": "oso-rhel7-zagg-web",
                "namespace": "default",
                "selfLink": "/oapi/v1/namespaces/default/imagestreams/oso-rhel7-zagg-web",
                "uid": "6ca2b199-dcdb-11e6-8ffd-0a5f8e3e32be",
                "resourceVersion": "8135944",
                "generation": 1,
                "creationTimestamp": "2017-01-17T17:36:05Z",
                "annotations": {
                    "openshift.io/image.dockerRepositoryCheck": "2017-01-17T17:36:05Z"
                }
            },
            "spec": {
                "tags": [
                    {
                        "name": "int",
                        "annotations": null,
                        "from": {
                            "kind": "DockerImage",
                            "name": "registry.ops.openshift.com/ops/oso-rhel7-zagg-web:int"
                        },
                        "generation": 1,
                        "importPolicy": {}
                    }
                ]
            },
            "status": {
                "dockerImageRepository": "172.30.183.164:5000/default/oso-rhel7-zagg-web",
                "tags": [
                    {
                        "tag": "int",
                        "items": [
                            {
                                "created": "2017-01-17T17:36:05Z",
                                "dockerImageReference": "registry.ops.openshift.com/ops/oso-rhel7-zagg-web@sha256:645bab780cf18a9b764d64b02ca65c39d13cb16f19badd0a49a1668629759392",
                                "image": "sha256:645bab780cf18a9b764d64b02ca65c39d13cb16f19badd0a49a1668629759392",
                                "generation": 1
                            }
                        ]
                    }
                ]
            }
        }
        '''
        
        mock_cmd.side_effect = [
            (0, istream, ''),
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mocked_kubeconfig',
        ]

        results = OCImage.run_ansible(params, False)

        self.assertFalse(results['changed'])
        self.assertEquals(results['results']['results'][0]['metadata']['name'], 'oso-rhel7-zagg-web')

    @mock.patch('oc_image.Utils.create_tmpfile_copy')
    @mock.patch('oc_image.OCImage._run')
    def test_state_present(self, mock_cmd, mock_tmpfile_copy):
        ''' Testing a image list '''
        params = {'registry_url': 'registry.ops.openshift.com',
                  'image_name': 'oso-rhel7-zagg-web',
                  'image_tag': 'int',
                  'name': 'default',
                  'namespace': 'default',
                  'state': 'present',
                  'kind': 'namespace',
                  'selector': None,
                  'kubeconfig': '/etc/origin/master/admin.kubeconfig',
                  'debug': False}


        istream = '''{
            "kind": "ImageStream",
            "apiVersion": "v1",
            "metadata": {
                "name": "oso-rhel7-zagg-web",
                "namespace": "default",
                "selfLink": "/oapi/v1/namespaces/default/imagestreams/oso-rhel7-zagg-web",
                "uid": "6ca2b199-dcdb-11e6-8ffd-0a5f8e3e32be",
                "resourceVersion": "8135944",
                "generation": 1,
                "creationTimestamp": "2017-01-17T17:36:05Z",
                "annotations": {
                    "openshift.io/image.dockerRepositoryCheck": "2017-01-17T17:36:05Z"
                }
            },
            "spec": {
                "tags": [
                    {
                        "name": "int",
                        "annotations": null,
                        "from": {
                            "kind": "DockerImage",
                            "name": "registry.ops.openshift.com/ops/oso-rhel7-zagg-web:int"
                        },
                        "generation": 1,
                        "importPolicy": {}
                    }
                ]
            },
            "status": {
                "dockerImageRepository": "172.30.183.164:5000/default/oso-rhel7-zagg-web",
                "tags": [
                    {
                        "tag": "int",
                        "items": [
                            {
                                "created": "2017-01-17T17:36:05Z",
                                "dockerImageReference": "registry.ops.openshift.com/ops/oso-rhel7-zagg-web@sha256:645bab780cf18a9b764d64b02ca65c39d13cb16f19badd0a49a1668629759392",
                                "image": "sha256:645bab780cf18a9b764d64b02ca65c39d13cb16f19badd0a49a1668629759392",
                                "generation": 1
                            }
                        ]
                    }
                ]
            }
        }
        '''
        istream1 = '''{
            "kind": "ImageStream",
            "apiVersion": "v1",
            "metadata": {
                "name": "oso-rhel7-zagg-web",
                "namespace": "default",
                "selfLink": "/oapi/v1/namespaces/default/imagestreams/oso-rhel7-zagg-web",
                "uid": "6ca2b199-dcdb-11e6-8ffd-0a5f8e3e32be",
                "resourceVersion": "8135944",
                "generation": 1,
                "creationTimestamp": "2017-01-17T17:36:05Z",
                "annotations": {
                    "openshift.io/image.dockerRepositoryCheck": "2017-01-17T17:36:05Z"
                }
            },
            "spec": {
                "tags": [
                    {
                        "name": "int",
                        "annotations": null,
                        "from": {
                            "kind": "DockerImage",
                            "name": "registry.ops.openshift.com/ops/oso-rhel7-zagg-web:int"
                        },
                        "generation": 1,
                        "importPolicy": {}
                    }
                ]
            },
            "status": {
                "dockerImageRepository": "172.30.183.164:5000/default/oso-rhel7-zagg-web",
                "tags": [
                    {
                        "tag": "int",
                        "items": [
                            {
                                "created": "2017-01-17T17:36:05Z",
                                "dockerImageReference": "registry.ops.openshift.com/ops/oso-rhel7-zagg-web@sha256:645bab780cf18a9b764d64b02ca65c39d13cb16f19badd0a49a1668629759392",
                                "image": "sha256:645bab780cf18a9b764d64b02ca65c39d13cb16f19badd0a49a1668629759392",
                                "generation": 1
                            }
                        ]
                    }
                ]
            }
        }
        '''


        mock_cmd.side_effect = [
            (0, istream, ''),
            (0, '', ''),
            (0, istream1, ''),
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mocked_kubeconfig',
        ]

        results = OCImage.run_ansible(params, False)

        self.assertTrue(results['changed'])
        self.assertTrue(results['results']['results']['labels'][0] ==
                        {'storage_pv_quota': 'False', 'awesomens': 'testinglabel'})

    def tearDown(self):
        '''TearDown method'''
        pass


if __name__ == "__main__":
    unittest.main()
