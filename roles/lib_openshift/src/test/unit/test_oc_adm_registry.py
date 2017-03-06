#!/usr/bin/env python
'''
 Unit tests for oc adm registry
'''
import mock

from lib_openshift.library import oc_adm_registry

MODULE_UNDER_TEST = oc_adm_registry
CLASS_UNDER_TEST = oc_adm_registry.Registry

DRY_RUN = '''{
    "kind": "List",
    "apiVersion": "v1",
    "metadata": {},
    "items": [
        {
            "kind": "ServiceAccount",
            "apiVersion": "v1",
            "metadata": {
                "name": "registry",
                "creationTimestamp": null
            }
        },
        {
            "kind": "ClusterRoleBinding",
            "apiVersion": "v1",
            "metadata": {
                "name": "registry-registry-role",
                "creationTimestamp": null
            },
            "userNames": [
                "system:serviceaccount:default:registry"
            ],
            "groupNames": null,
            "subjects": [
                {
                    "kind": "ServiceAccount",
                    "namespace": "default",
                    "name": "registry"
                }
            ],
            "roleRef": {
                "kind": "ClusterRole",
                "name": "system:registry"
            }
        },
        {
            "kind": "DeploymentConfig",
            "apiVersion": "v1",
            "metadata": {
                "name": "docker-registry",
                "creationTimestamp": null,
                "labels": {
                    "docker-registry": "default"
                }
            },
            "spec": {
                "strategy": {
                    "resources": {}
                },
                "triggers": [
                    {
                        "type": "ConfigChange"
                    }
                ],
                "replicas": 1,
                "test": false,
                "selector": {
                    "docker-registry": "default"
                },
                "template": {
                    "metadata": {
                        "creationTimestamp": null,
                        "labels": {
                            "docker-registry": "default"
                        }
                    },
                    "spec": {
                        "volumes": [
                            {
                                "name": "registry-storage",
                                "emptyDir": {}
                            }
                        ],
                        "containers": [
                            {
                                "name": "registry",
                                "image": "openshift3/ose-docker-registry:v3.5.0.39",
                                "ports": [
                                    {
                                        "containerPort": 5000
                                    }
                                ],
                                "env": [
                                    {
                                        "name": "REGISTRY_HTTP_ADDR",
                                        "value": ":5000"
                                    },
                                    {
                                        "name": "REGISTRY_HTTP_NET",
                                        "value": "tcp"
                                    },
                                    {
                                        "name": "REGISTRY_HTTP_SECRET",
                                        "value": "WQjSGeUu5KFZRTwGeIXgwIjyraNDLmdJblsFbtzZdF8="
                                    },
                                    {
                                        "name": "REGISTRY_MIDDLEWARE_REPOSITORY_OPENSHIFT_ENFORCEQUOTA",
                                        "value": "false"
                                    }
                                ],
                                "resources": {
                                    "requests": {
                                        "cpu": "100m",
                                        "memory": "256Mi"
                                    }
                                },
                                "volumeMounts": [
                                    {
                                        "name": "registry-storage",
                                        "mountPath": "/registry"
                                    }
                                ],
                                "livenessProbe": {
                                    "httpGet": {
                                        "path": "/healthz",
                                        "port": 5000
                                    },
                                    "initialDelaySeconds": 10,
                                    "timeoutSeconds": 5
                                },
                                "readinessProbe": {
                                    "httpGet": {
                                        "path": "/healthz",
                                        "port": 5000
                                    },
                                    "timeoutSeconds": 5
                                },
                                "securityContext": {
                                    "privileged": false
                                }
                            }
                        ],
                        "nodeSelector": {
                            "type": "infra"
                        },
                        "serviceAccountName": "registry",
                        "serviceAccount": "registry"
                    }
                }
            },
            "status": {
                "latestVersion": 0,
                "observedGeneration": 0,
                "replicas": 0,
                "updatedReplicas": 0,
                "availableReplicas": 0,
                "unavailableReplicas": 0
            }
        },
        {
            "kind": "Service",
            "apiVersion": "v1",
            "metadata": {
                "name": "docker-registry",
                "creationTimestamp": null,
                "labels": {
                    "docker-registry": "default"
                }
            },
            "spec": {
                "ports": [
                    {
                        "name": "5000-tcp",
                        "port": 5000,
                        "targetPort": 5000
                    }
                ],
                "selector": {
                    "docker-registry": "default"
                },
                "clusterIP": "172.30.119.110",
                "sessionAffinity": "ClientIP"
            },
            "status": {
                "loadBalancer": {}
            }
        }
    ]}'''


def test_state_present(mock_run_cmd):
    ''' Testing state present '''
    params = {'state': 'present',
              'debug': False,
              'namespace': 'default',
              'name': 'docker-registry',
              'kubeconfig': '/etc/origin/master/admin.kubeconfig',
              'images': None,
              'latest_images': None,
              'labels': None,
              'ports': ['5000'],
              'replicas': 1,
              'selector': 'type=infra',
              'service_account': 'registry',
              'mount_host': None,
              'volume_mounts': None,
              'env_vars': {},
              'enforce_quota': False,
              'force': False,
              'daemonset': False,
              'tls_key': None,
              'tls_certificate': None,
              'edits': []}

    mock_run_cmd.side_effect = [
        (1, '', 'Error from server (NotFound): deploymentconfigs "docker-registry" not found'),
        (1, '', 'Error from server (NotFound): service "docker-registry" not found'),
        (0, DRY_RUN, ''),
        (0, '', ''),
        (0, '', ''),
    ]

    results = CLASS_UNDER_TEST.run_ansible(params, False)

    assert results['changed']
    for result in results['results']['results']:
        assert result['returncode'] == 0

    mock_run_cmd.assert_has_calls([
        mock.call(['oc', 'get', 'dc', 'docker-registry', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'get', 'svc', 'docker-registry', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'adm', 'registry', '--daemonset=False', '--enforce-quota=False',
                   '--ports=5000', '--replicas=1', '--selector=type=infra',
                   '--service-account=registry', '--dry-run=True', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'create', '-f', mock.ANY, '-n', 'default'], None),
        mock.call(['oc', 'create', '-f', mock.ANY, '-n', 'default'], None), ])
