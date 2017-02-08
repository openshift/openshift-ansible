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

    @mock.patch('oc_env.OCEnv._run')
    def test_listing_all_env_vars(self, mock_cmd):
        ''' Testing listing all environment variables from a dc'''

        # Arrange

        # run_ansible input parameters
        params = {
            'state': 'list',
            'namespace': 'default',
            'name': 'router',
            'kind': 'dc',
            'list_all': False,
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
                "resourceVersion": "513678",
                "selfLink": "/oapi/v1/namespaces/default/deploymentconfigs/router",
                "uid": "7c705902-e960-11e6-b041-0ed9df7abc38"
            },
            "spec": {
                "replicas": 2,
                "selector": {
                    "router": "router"
                },
                "strategy": {
                    "activeDeadlineSeconds": 21600,
                    "resources": {},
                    "rollingParams": {
                        "intervalSeconds": 1,
                        "maxSurge": "50%",
                        "maxUnavailable": "50%",
                        "timeoutSeconds": 600,
                        "updatePeriodSeconds": 1
                    },
                    "type": "Rolling"
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
                                        "name": "ROUTER_EXTERNAL_HOST_INTERNAL_ADDRESS"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_PARTITION_PATH"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_PASSWORD"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_PRIVKEY",
                                        "value": "/etc/secret-volume/router.pem"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_USERNAME"
                                    },
                                    {
                                        "name": "ROUTER_EXTERNAL_HOST_VXLAN_GW_CIDR"
                                    },
                                    {
                                        "name": "ROUTER_SERVICE_HTTPS_PORT",
                                        "value": "443"
                                    },
                                    {
                                        "name": "ROUTER_SERVICE_HTTP_PORT",
                                        "value": "80"
                                    },
                                    {
                                        "name": "ROUTER_SERVICE_NAME",
                                        "value": "router"
                                    },
                                    {
                                        "name": "ROUTER_SERVICE_NAMESPACE",
                                        "value": "default"
                                    },
                                    {
                                        "name": "ROUTER_SUBDOMAIN"
                                    },
                                    {
                                        "name": "STATS_PASSWORD",
                                        "value": "UEKR5GCWGI"
                                    },
                                    {
                                        "name": "STATS_PORT",
                                        "value": "1936"
                                    },
                                    {
                                        "name": "STATS_USERNAME",
                                        "value": "admin"
                                    },
                                    {
                                        "name": "EXTENDED_VALIDATION",
                                        "value": "false"
                                    },
                                    {
                                        "name": "ROUTER_USE_PROXY_PROTOCOL",
                                        "value": "true"
                                    }
                                ],
                                "image": "openshift3/ose-haproxy-router:v3.5.0.17",
                                "imagePullPolicy": "IfNotPresent",
                                "livenessProbe": {
                                    "failureThreshold": 3,
                                    "httpGet": {
                                        "host": "localhost",
                                        "path": "/healthz",
                                        "port": 1936,
                                        "scheme": "HTTP"
                                    },
                                    "initialDelaySeconds": 10,
                                    "periodSeconds": 10,
                                    "successThreshold": 1,
                                    "timeoutSeconds": 1
                                },
                                "name": "router",
                                "ports": [
                                    {
                                        "containerPort": 80,
                                        "hostPort": 80,
                                        "protocol": "TCP"
                                    },
                                    {
                                        "containerPort": 443,
                                        "hostPort": 443,
                                        "protocol": "TCP"
                                    },
                                    {
                                        "containerPort": 5000,
                                        "hostPort": 5000,
                                        "protocol": "TCP"
                                    },
                                    {
                                        "containerPort": 1936,
                                        "hostPort": 1936,
                                        "name": "stats",
                                        "protocol": "TCP"
                                    }
                                ],
                                "readinessProbe": {
                                    "failureThreshold": 3,
                                    "httpGet": {
                                        "host": "localhost",
                                        "path": "/healthz",
                                        "port": 1936,
                                        "scheme": "HTTP"
                                    },
                                    "initialDelaySeconds": 10,
                                    "periodSeconds": 10,
                                    "successThreshold": 1,
                                    "timeoutSeconds": 1
                                },
                                "resources": {
                                    "requests": {
                                        "cpu": "100m",
                                        "memory": "256Mi"
                                    }
                                },
                                "terminationMessagePath": "/dev/termination-log",
                                "volumeMounts": [
                                    {
                                        "mountPath": "/etc/pki/tls/private",
                                        "name": "server-certificate",
                                        "readOnly": true
                                    }
                                ]
                            }
                        ],
                        "dnsPolicy": "ClusterFirst",
                        "hostNetwork": true,
                        "nodeSelector": {
                            "type": "infra"
                        },
                        "restartPolicy": "Always",
                        "securityContext": {},
                        "serviceAccount": "router",
                        "serviceAccountName": "router",
                        "terminationGracePeriodSeconds": 30,
                        "volumes": [
                            {
                                "name": "server-certificate",
                                "secret": {
                                    "defaultMode": 420,
                                    "secretName": "router-certs"
                                }
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
            },
            "status": {
                "availableReplicas": 2,
                "conditions": [
                    {
                        "lastTransitionTime": "2017-02-02T15:59:12Z",
                        "lastUpdateTime": null,
                        "message": "Deployment config has minimum availability.",
                        "status": "True",
                        "type": "Available"
                    },
                    {
                        "lastTransitionTime": "2017-02-07T19:55:26Z",
                        "lastUpdateTime": "2017-02-07T19:55:26Z",
                        "message": "replication controller router-2 has failed progressing",
                        "reason": "ProgressDeadlineExceeded",
                        "status": "False",
                        "type": "Progressing"
                    }
                ],
                "details": {
                    "causes": [
                        {
                            "type": "ConfigChange"
                        }
                    ],
                    "message": "config change"
                },
                "latestVersion": 2,
                "observedGeneration": 8,
                "readyReplicas": 2,
                "replicas": 2,
                "unavailableReplicas": 0,
                "updatedReplicas": 0
            }
        }'''

        # Return values of our mocked function call. These get returned once per call.
        mock_cmd.side_effect = [
            (0, dc_results, ''),  # First call to the mock
        ]

        # Act
        results = OCEnv.run_ansible(params, False)

        # Assert
        self.assertFalse(results['changed'])
        for env_var in results['results']:
	    if env_var == {'name': 'DEFAULT_CERTIFICATE_DIR', 'value': '/etc/pki/tls/private'}:
                break
        else:
            self.fail('Did not find envionrment variables in results.')
        self.assertEqual(results['state'], 'list')

        # Making sure our mocks were called as we expected
        mock_cmd.assert_has_calls([
            mock.call(['oc', '-n', 'default', 'get', 'dc', 'router', '-o', 'json'], None),
        ])

#    @mock.patch('oc_serviceaccount_secret.Yedit._write')
#    @mock.patch('oc_serviceaccount_secret.OCServiceAccountSecret._run')
#    def test_removing_a_secret_to_a_serviceaccount(self, mock_cmd, mock_write):
#        ''' Testing adding a secret to a service account '''
#
#        # Arrange
#
#        # run_ansible input parameters
#        params = {
#            'state': 'absent',
#            'namespace': 'default',
#            'secret': 'newsecret',
#            'service_account': 'builder',
#            'kubeconfig': '/etc/origin/master/admin.kubeconfig',
#            'debug': False,
#        }
#
#        oc_get_sa_before = '''{
#            "kind": "ServiceAccount",
#            "apiVersion": "v1",
#            "metadata": {
#                "name": "builder",
#                "namespace": "default",
#                "selfLink": "/api/v1/namespaces/default/serviceaccounts/builder",
#                "uid": "cf47bca7-ebc4-11e6-b041-0ed9df7abc38",
#                "resourceVersion": "302879",
#                "creationTimestamp": "2017-02-05T17:02:00Z"
#            },
#            "secrets": [
#                {
#                    "name": "builder-dockercfg-rsrua"
#                },
#                {
#                    "name": "builder-token-akqxi"
#                },
#                {
#                    "name": "newsecret"
#                }
#
#            ],
#            "imagePullSecrets": [
#                {
#                    "name": "builder-dockercfg-rsrua"
#                }
#            ]
#        }
#        '''
#
#        builder_yaml_file = '''\
#secrets:
#- name: builder-dockercfg-rsrua
#- name: builder-token-akqxi
#kind: ServiceAccount
#imagePullSecrets:
#- name: builder-dockercfg-rsrua
#apiVersion: v1
#metadata:
#  name: builder
#  namespace: default
#  resourceVersion: '302879'
#  creationTimestamp: '2017-02-05T17:02:00Z'
#  selfLink: /api/v1/namespaces/default/serviceaccounts/builder
#  uid: cf47bca7-ebc4-11e6-b041-0ed9df7abc38
#'''
#
#        # Return values of our mocked function call. These get returned once per call.
#        mock_cmd.side_effect = [
#            (0, oc_get_sa_before, ''),  # First call to the mock
#            (0, oc_get_sa_before, ''),  # Second call to the mock
#            (0, 'serviceaccount "builder" replaced', ''),  # Third call to the mock
#        ]
#
#        # Act
#        results = OCServiceAccountSecret.run_ansible(params, False)
#
#        # Assert
#        self.assertTrue(results['changed'])
#        self.assertEqual(results['results']['returncode'], 0)
#        self.assertEqual(results['state'], 'absent')
#
#        # Making sure our mocks were called as we expected
#        mock_cmd.assert_has_calls([
#            mock.call(['oc', '-n', 'default', 'get', 'sa', 'builder', '-o', 'json'], None),
#            mock.call(['oc', '-n', 'default', 'get', 'sa', 'builder', '-o', 'json'], None),
#            mock.call(['oc', '-n', 'default', 'replace', '-f', '/tmp/builder'], None),
#        ])
#
#        mock_write.assert_has_calls([
#            mock.call('/tmp/builder', builder_yaml_file)
#        ])

    def tearDown(self):
        '''TearDown method'''
        pass


if __name__ == "__main__":
    unittest.main()
