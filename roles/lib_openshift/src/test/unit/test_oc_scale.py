'''
 Unit tests for oc scale
'''
import json

from lib_openshift.library import oc_scale

MODULE_UNDER_TEST = oc_scale
CLASS_UNDER_TEST = oc_scale.OCScale


def test_state_list(mock_run_cmd):
    ''' Testing a get '''
    params = {'name': 'router',
              'namespace': 'default',
              'replicas': 2,
              'state': 'list',
              'kind': 'dc',
              'kubeconfig': '/etc/origin/master/admin.kubeconfig',
              'debug': False}

    dc = {
        "kind": "DeploymentConfig",
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
    }

    mock_run_cmd.side_effect = [
        (0, json.dumps(dc), '')
    ]

    results = CLASS_UNDER_TEST.run_ansible(params, False)

    assert results['changed'] is False
    assert results['result'][0] == 2


def test_scale(mock_run_cmd):
    ''' Testing a get '''
    params = {'name': 'router',
              'namespace': 'default',
              'replicas': 3,
              'state': 'list',
              'kind': 'dc',
              'kubeconfig': '/etc/origin/master/admin.kubeconfig',
              'debug': False}

    dc = {
        "kind": "DeploymentConfig",
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
    }

    mock_run_cmd.side_effect = [
        (0, json.dumps(dc), ''),
        (0, '', '')
    ]

    results = CLASS_UNDER_TEST.run_ansible(params, False)

    assert results['changed'] is False
    assert results['result'][0] == 3


def test_no_dc_scale(mock_run_cmd):
    ''' Testing a get '''
    params = {'name': 'not_there',
              'namespace': 'default',
              'replicas': 3,
              'state': 'present',
              'kind': 'dc',
              'kubeconfig': '/etc/origin/master/admin.kubeconfig',
              'debug': False}

    mock_run_cmd.side_effect = [
        (1, '', "Error from server: deploymentconfigs \"not_there\" not found\n")
    ]

    results = CLASS_UNDER_TEST.run_ansible(params, False)

    assert results['failed']
    assert results['msg']['returncode'] == 1
