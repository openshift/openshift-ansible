#!/usr/bin/env python2
'''
 Unit tests for oc_env
'''
# To run:
# ./oc_env.py
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
from oc_env import OCEnv  # noqa: E402


class OCEnvTest(unittest.TestCase):
    '''
     Test class for OCEnv
    '''

    def setUp(self):
        ''' setup method will create a file and set to known configuration '''
        pass

    @mock.patch('oc_env.Utils.create_tmpfile_copy')
    @mock.patch('oc_env.OCEnv._run')
    def test_listing_all_env_vars(self, mock_cmd, mock_tmpfile_copy):
        ''' Testing listing all environment variables from a dc'''

        # Arrange

        # run_ansible input parameters
        params = {
            'state': 'list',
            'namespace': 'default',
            'name': 'router',
            'kind': 'dc',
            'env_vars': None,
            'kubeconfig': '/etc/origin/master/admin.kubeconfig',
            'debug': False,
        }

        dc_results = '''{
            "apiVersion": "v1",
            "kind": "DeploymentConfig",
            "metadata": {
                "creationTimestamp": "2017-02-02T15:58:49Z",
                "generation": 8,
                "labels": {
                    "router": "router"
                },
                "name": "router",
                "namespace": "default",
                "resourceVersion": "513678"
            },
            "spec": {
                "replicas": 2,
                "selector": {
                    "router": "router"
                },
                "template": {
                    "metadata": {
                        "creationTimestamp": null,
                        "labels": {
                            "router": "router"
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "env": [
                                    {
                                        "name": "DEFAULT_CERTIFICATE_DIR",
                                        "value": "/etc/pki/tls/private"
                                    },
                                    {
                                        "name": "DEFAULT_CERTIFICATE_PATH",
                                        "value": "/etc/pki/tls/private/tls.crt"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_HOSTNAME"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_HTTPS_VSERVER"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_HTTP_VSERVER"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_INSECURE",
                                        "value": "false"
                                    }
                                ],
                                "name": "router"
                            }
                        ]
                    }
                },
                "test": false,
                "triggers": [
                    {
                        "type": "ConfigChange"
                    }
                ]
            }
        }'''

        # Return values of our mocked function call. These get returned once per call.
        mock_cmd.side_effect = [
            (0, dc_results, ''),  # First call to the mock
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mock_adminkubeconfig',
        ]

        # Act
        results = OCEnv.run_ansible(params, False)

        # Assert
        self.assertFalse(results['changed'])
        for env_var in results['results']:
            if env_var == {'name': 'DEFAULT_CERTIFICATE_DIR', 'value': '/etc/pki/tls/private'}:
                break
        else:
            self.fail('Did not find environment variables in results.')
        self.assertEqual(results['state'], 'list')

        # Making sure our mocks were called as we expected
        mock_cmd.assert_has_calls([
            mock.call(['oc', '-n', 'default', 'get', 'dc', 'router', '-o', 'json'], None),
        ])

    @mock.patch('oc_env.Utils.create_tmpfile_copy')
    @mock.patch('oc_env.OCEnv._run')
    def test_adding_env_vars(self, mock_cmd, mock_tmpfile_copy):
        ''' Test add environment variables to a dc'''

        # Arrange

        # run_ansible input parameters
        params = {
            'state': 'present',
            'namespace': 'default',
            'name': 'router',
            'kind': 'dc',
            'kubeconfig': '/etc/origin/master/admin.kubeconfig',
            'debug': False,
            'env_vars': {'SOMEKEY': 'SOMEVALUE'},
        }

        dc_results = '''{
            "apiVersion": "v1",
            "kind": "DeploymentConfig",
            "metadata": {
                "creationTimestamp": "2017-02-02T15:58:49Z",
                "generation": 8,
                "labels": {
                    "router": "router"
                },
                "name": "router",
                "namespace": "default",
                "resourceVersion": "513678"
            },
            "spec": {
                "replicas": 2,
                "selector": {
                    "router": "router"
                },
                "template": {
                    "metadata": {
                        "creationTimestamp": null,
                        "labels": {
                            "router": "router"
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "env": [
                                    {
                                        "name": "DEFAULT_CERTIFICATE_DIR",
                                        "value": "/etc/pki/tls/private"
                                    },
                                    {
                                        "name": "DEFAULT_CERTIFICATE_PATH",
                                        "value": "/etc/pki/tls/private/tls.crt"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_HOSTNAME"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_HTTPS_VSERVER"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_HTTP_VSERVER"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_INSECURE",
                                        "value": "false"
                                    }
                                ],
                                "name": "router"
                            }
                        ]
                    }
                },
                "test": false,
                "triggers": [
                    {
                        "type": "ConfigChange"
                    }
                ]
            }
        }'''

        dc_results_after = '''{
            "apiVersion": "v1",
            "kind": "DeploymentConfig",
            "metadata": {
                "creationTimestamp": "2017-02-02T15:58:49Z",
                "generation": 8,
                "labels": {
                    "router": "router"
                },
                "name": "router",
                "namespace": "default",
                "resourceVersion": "513678"
            },
            "spec": {
                "replicas": 2,
                "selector": {
                    "router": "router"
                },
                "template": {
                    "metadata": {
                        "creationTimestamp": null,
                        "labels": {
                            "router": "router"
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "env": [
                                    {
                                        "name": "DEFAULT_CERTIFICATE_DIR",
                                        "value": "/etc/pki/tls/private"
                                    },
                                    {
                                        "name": "DEFAULT_CERTIFICATE_PATH",
                                        "value": "/etc/pki/tls/private/tls.crt"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_HOSTNAME"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_HTTPS_VSERVER"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_HTTP_VSERVER"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_INSECURE",
                                        "value": "false"
                                    },
                                    {
                                        "name": "SOMEKEY",
                                        "value": "SOMEVALUE"
                                    }
                                ],
                                "name": "router"
                            }
                        ]
                    }
                },
                "test": false,
                "triggers": [
                    {
                        "type": "ConfigChange"
                    }
                ]
            }
        }'''

        # Return values of our mocked function call. These get returned once per call.
        mock_cmd.side_effect = [
            (0, dc_results, ''),
            (0, dc_results, ''),
            (0, dc_results_after, ''),
            (0, dc_results_after, ''),
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mock_adminkubeconfig',
        ]

        # Act
        results = OCEnv.run_ansible(params, False)

        # Assert
        self.assertTrue(results['changed'])
        for env_var in results['results']:
            if env_var == {'name': 'SOMEKEY', 'value': 'SOMEVALUE'}:
                break
        else:
            self.fail('Did not find environment variables in results.')
        self.assertEqual(results['state'], 'present')

        # Making sure our mocks were called as we expected
        mock_cmd.assert_has_calls([
            mock.call(['oc', '-n', 'default', 'get', 'dc', 'router', '-o', 'json'], None),
        ])

    @mock.patch('oc_env.Utils.create_tmpfile_copy')
    @mock.patch('oc_env.OCEnv._run')
    def test_removing_env_vars(self, mock_cmd, mock_tmpfile_copy):
        ''' Test add environment variables to a dc'''

        # Arrange

        # run_ansible input parameters
        params = {
            'state': 'absent',
            'namespace': 'default',
            'name': 'router',
            'kind': 'dc',
            'kubeconfig': '/etc/origin/master/admin.kubeconfig',
            'debug': False,
            'env_vars': {'SOMEKEY': 'SOMEVALUE'},
        }

        dc_results_before = '''{
            "apiVersion": "v1",
            "kind": "DeploymentConfig",
            "metadata": {
                "creationTimestamp": "2017-02-02T15:58:49Z",
                "generation": 8,
                "labels": {
                    "router": "router"
                },
                "name": "router",
                "namespace": "default",
                "resourceVersion": "513678"
            },
            "spec": {
                "replicas": 2,
                "selector": {
                    "router": "router"
                },
                "template": {
                    "metadata": {
                        "creationTimestamp": null,
                        "labels": {
                            "router": "router"
                        }
                    },
                    "spec": {
                        "containers": [
                            {
                                "env": [
                                    {
                                        "name": "DEFAULT_CERTIFICATE_DIR",
                                        "value": "/etc/pki/tls/private"
                                    },
                                    {
                                        "name": "DEFAULT_CERTIFICATE_PATH",
                                        "value": "/etc/pki/tls/private/tls.crt"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_HOSTNAME"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_HTTPS_VSERVER"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_HTTP_VSERVER"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_INSECURE",
                                        "value": "false"
                                    },
                                    {
                                        "name": "SOMEKEY",
                                        "value": "SOMEVALUE"
                                    }
                                ],
                                "name": "router"
                            }
                        ]
                    }
                },
                "test": false,
                "triggers": [
                    {
                        "type": "ConfigChange"
                    }
                ]
            }
        }'''

        # Return values of our mocked function call. These get returned once per call.
        mock_cmd.side_effect = [
            (0, dc_results_before, ''),
            (0, dc_results_before, ''),
            (0, '', ''),
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mock_adminkubeconfig',
        ]

        # Act
        results = OCEnv.run_ansible(params, False)

        # Assert
        self.assertTrue(results['changed'])
        self.assertEqual(results['state'], 'absent')

        # Making sure our mocks were called as we expected
        mock_cmd.assert_has_calls([
            mock.call(['oc', '-n', 'default', 'get', 'dc', 'router', '-o', 'json'], None),
        ])

    def tearDown(self):
        '''TearDown method'''
        pass


if __name__ == "__main__":
    unittest.main()
