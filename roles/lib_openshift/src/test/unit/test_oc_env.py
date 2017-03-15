'''
 Unit tests for oc_env
'''
import mock
import pytest

from lib_openshift.library import oc_env

MODULE_UNDER_TEST = oc_env
CLASS_UNDER_TEST = oc_env.OCEnv


def test_listing_all_env_vars(mock_run_cmd):
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
    mock_run_cmd.side_effect = [
        (0, dc_results, ''),  # First call to the mock
    ]

    # Act
    results = CLASS_UNDER_TEST.run_ansible(params, False)

    # Assert
    assert results['changed'] is False
    for env_var in results['results']:
        if env_var == {'name': 'DEFAULT_CERTIFICATE_DIR', 'value': '/etc/pki/tls/private'}:
            break
    else:
        pytest.fail('Did not find environment variables in results.')

    assert results['state'] == 'list'

    # Making sure our mocks were called as we expected
    mock_run_cmd.assert_has_calls([
        mock.call(['oc', 'get', 'dc', 'router', '-o', 'json', '-n', 'default'], None),
    ])


def test_adding_env_vars(mock_run_cmd):
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
    mock_run_cmd.side_effect = [
        (0, dc_results, ''),
        (0, dc_results, ''),
        (0, dc_results_after, ''),
        (0, dc_results_after, ''),
    ]

    # Act
    results = CLASS_UNDER_TEST.run_ansible(params, False)

    # Assert
    assert results['changed'] is True
    for env_var in results['results']:
        if env_var == {'name': 'SOMEKEY', 'value': 'SOMEVALUE'}:
            break
    else:
        pytest.fail('Did not find environment variables in results.')

    assert results['state'] == 'present'

    # Making sure our mocks were called as we expected
    mock_run_cmd.assert_has_calls([
        mock.call(['oc', 'get', 'dc', 'router', '-o', 'json', '-n', 'default'], None),
    ])


def test_removing_env_vars(mock_run_cmd):
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
    mock_run_cmd.side_effect = [
        (0, dc_results_before, ''),
        (0, dc_results_before, ''),
        (0, '', ''),
    ]

    # Act
    results = CLASS_UNDER_TEST.run_ansible(params, False)

    # Assert
    assert results['changed'] is True
    assert results['state'] == 'absent'

    # Making sure our mocks were called as we expected
    mock_run_cmd.assert_has_calls([
        mock.call(['oc', 'get', 'dc', 'router', '-o', 'json', '-n', 'default'], None),
    ])
