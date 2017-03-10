#!/usr/bin/env python
'''
 Unit tests for oc adm router
'''
import mock

from lib_openshift.library import oc_adm_router

MODULE_UNDER_TEST = oc_adm_router
CLASS_UNDER_TEST = oc_adm_router.Router

DRY_RUN = '''{
"kind": "List",
"apiVersion": "v1",
"metadata": {},
"items": [
    {
        "kind": "ServiceAccount",
        "apiVersion": "v1",
        "metadata": {
            "name": "router",
            "creationTimestamp": null
        }
    },
    {
        "kind": "ClusterRoleBinding",
        "apiVersion": "v1",
        "metadata": {
            "name": "router-router-role",
            "creationTimestamp": null
        },
        "userNames": [
            "system:serviceaccount:default:router"
        ],
        "groupNames": null,
        "subjects": [
            {
                "kind": "ServiceAccount",
                "namespace": "default",
                "name": "router"
            }
        ],
        "roleRef": {
            "kind": "ClusterRole",
            "name": "system:router"
        }
    },
    {
        "kind": "DeploymentConfig",
        "apiVersion": "v1",
        "metadata": {
            "name": "router",
            "creationTimestamp": null,
            "labels": {
                "router": "router"
            }
        },
        "spec": {
            "strategy": {
                "type": "Rolling",
                "rollingParams": {
                    "maxUnavailable": "25%",
                    "maxSurge": 0
                },
                "resources": {}
            },
            "triggers": [
                {
                    "type": "ConfigChange"
                }
            ],
            "replicas": 2,
            "test": false,
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
                    "volumes": [
                        {
                            "name": "server-certificate",
                            "secret": {
                                "secretName": "router-certs"
                            }
                        }
                    ],
                    "containers": [
                        {
                            "name": "router",
                            "image": "openshift3/ose-haproxy-router:v3.5.0.39",
                            "ports": [
                                {
                                    "containerPort": 80
                                },
                                {
                                    "containerPort": 443
                                },
                                {
                                    "name": "stats",
                                    "containerPort": 1936,
                                    "protocol": "TCP"
                                }
                            ],
                            "env": [
                                {
                                    "name": "DEFAULT_CERTIFICATE_DIR",
                                    "value": "/etc/pki/tls/private"
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
                                    "value": "eSfUICQyyr"
                                },
                                {
                                    "name": "STATS_PORT",
                                    "value": "1936"
                                },
                                {
                                    "name": "STATS_USERNAME",
                                    "value": "admin"
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
                                    "name": "server-certificate",
                                    "readOnly": true,
                                    "mountPath": "/etc/pki/tls/private"
                                }
                            ],
                            "livenessProbe": {
                                "httpGet": {
                                    "path": "/healthz",
                                    "port": 1936,
                                    "host": "localhost"
                                },
                                "initialDelaySeconds": 10
                            },
                            "readinessProbe": {
                                "httpGet": {
                                    "path": "/healthz",
                                    "port": 1936,
                                    "host": "localhost"
                                },
                                "initialDelaySeconds": 10
                            },
                            "imagePullPolicy": "IfNotPresent"
                        }
                    ],
                    "nodeSelector": {
                        "type": "infra"
                    },
                    "serviceAccountName": "router",
                    "serviceAccount": "router",
                    "hostNetwork": true,
                    "securityContext": {}
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
            "name": "router",
            "creationTimestamp": null,
            "labels": {
                "router": "router"
            },
            "annotations": {
                "service.alpha.openshift.io/serving-cert-secret-name": "router-certs"
            }
        },
        "spec": {
            "ports": [
                {
                    "name": "80-tcp",
                    "port": 80,
                    "targetPort": 80
                },
                {
                    "name": "443-tcp",
                    "port": 443,
                    "targetPort": 443
                },
                {
                    "name": "1936-tcp",
                    "protocol": "TCP",
                    "port": 1936,
                    "targetPort": 1936
                }
            ],
            "selector": {
                "router": "router"
            }
        },
        "status": {
            "loadBalancer": {}
        }
    }
]
}'''


def test_state_present(mock_run_cmd):
    ''' Testing a create '''
    params = {'state': 'present',
              'debug': False,
              'namespace': 'default',
              'name': 'router',
              'default_cert': None,
              'cert_file': None,
              'key_file': None,
              'cacert_file': None,
              'labels': None,
              'ports': ['80:80', '443:443'],
              'images': None,
              'latest_images': None,
              'clusterip': None,
              'portalip': None,
              'session_affinity': None,
              'service_type': None,
              'kubeconfig': '/etc/origin/master/admin.kubeconfig',
              'replicas': 2,
              'selector': 'type=infra',
              'service_account': 'router',
              'router_type': None,
              'host_network': None,
              'external_host': None,
              'external_host_vserver': None,
              'external_host_insecure': False,
              'external_host_partition_path': None,
              'external_host_username': None,
              'external_host_password': None,
              'external_host_private_key': None,
              'expose_metrics': False,
              'metrics_image': None,
              'stats_user': None,
              'stats_password': None,
              'stats_port': 1936,
              'edits': []}

    mock_run_cmd.side_effect = [
        (1, '', 'Error from server (NotFound): deploymentconfigs "router" not found'),
        (1, '', 'Error from server (NotFound): service "router" not found'),
        (1, '', 'Error from server (NotFound): serviceaccount "router" not found'),
        (1, '', 'Error from server (NotFound): secret "router-certs" not found'),
        (1, '', 'Error from server (NotFound): clsuterrolebinding "router-router-role" not found'),
        (0, DRY_RUN, ''),
        (0, '', ''),
        (0, '', ''),
        (0, '', ''),
        (0, '', ''),
        (0, '', ''),
    ]

    results = CLASS_UNDER_TEST.run_ansible(params, False)

    assert results['changed'] is True
    for result in results['results']['results']:
        assert result['returncode'] == 0

    mock_run_cmd.assert_has_calls([
        mock.call(['oc', 'get', 'dc', 'router', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'get', 'svc', 'router', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'get', 'sa', 'router', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'get', 'secret', 'router-certs', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'get', 'clusterrolebinding', 'router-router-role', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'adm', 'router', 'router', '--expose-metrics=False', '--external-host-insecure=False',
                   '--ports=80:80,443:443', '--replicas=2', '--selector=type=infra', '--service-account=router',
                   '--stats-port=1936', '--dry-run=True', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'create', '-f', mock.ANY, '-n', 'default'], None),
        mock.call(['oc', 'create', '-f', mock.ANY, '-n', 'default'], None),
        mock.call(['oc', 'create', '-f', mock.ANY, '-n', 'default'], None),
        mock.call(['oc', 'create', '-f', mock.ANY, '-n', 'default'], None)])
