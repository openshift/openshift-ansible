'''
 Unit tests for oc service
'''
from lib_openshift.library import oc_service

MODULE_UNDER_TEST = oc_service
CLASS_UNDER_TEST = oc_service.OCService


def test_state_list(mock_run_cmd):
    ''' Testing a get '''
    params = {'name': 'router',
              'namespace': 'default',
              'ports': None,
              'state': 'list',
              'labels': None,
              'clusterip': None,
              'portalip': None,
              'selector': None,
              'session_affinity': None,
              'service_type': None,
              'kubeconfig': '/etc/origin/master/admin.kubeconfig',
              'debug': False}

    service = '''{
        "kind": "Service",
        "apiVersion": "v1",
        "metadata": {
            "name": "router",
            "namespace": "default",
            "selfLink": "/api/v1/namespaces/default/services/router",
            "uid": "fabd2440-e3d8-11e6-951c-0e3dd518cefa",
            "resourceVersion": "3206",
            "creationTimestamp": "2017-01-26T15:06:14Z",
            "labels": {
                "router": "router"
            }
        },
        "spec": {
            "ports": [
                {
                    "name": "80-tcp",
                    "protocol": "TCP",
                    "port": 80,
                    "targetPort": 80
                },
                {
                    "name": "443-tcp",
                    "protocol": "TCP",
                    "port": 443,
                    "targetPort": 443
                },
                {
                    "name": "1936-tcp",
                    "protocol": "TCP",
                    "port": 1936,
                    "targetPort": 1936
                },
                {
                    "name": "5000-tcp",
                    "protocol": "TCP",
                    "port": 5000,
                    "targetPort": 5000
                }
            ],
            "selector": {
                "router": "router"
            },
            "clusterIP": "172.30.129.161",
            "type": "ClusterIP",
            "sessionAffinity": "None"
        },
        "status": {
            "loadBalancer": {}
        }
    }'''
    mock_run_cmd.side_effect = [
        (0, service, '')
    ]

    results = CLASS_UNDER_TEST.run_ansible(params, False)

    assert results['changed'] is False
    assert results['results']['results'][0]['metadata']['name'] == 'router'


def test_create(mock_run_cmd):
    ''' Testing a create service '''
    params = {'name': 'router',
              'namespace': 'default',
              'ports': {'name': '9000-tcp',
                        'port': 9000,
                        'protocol': 'TCP',
                        'targetPOrt': 9000},
              'state': 'present',
              'labels': None,
              'clusterip': None,
              'portalip': None,
              'selector': {'router': 'router'},
              'session_affinity': 'ClientIP',
              'service_type': 'ClusterIP',
              'kubeconfig': '/etc/origin/master/admin.kubeconfig',
              'debug': False}

    service = '''{
        "kind": "Service",
        "apiVersion": "v1",
        "metadata": {
            "name": "router",
            "namespace": "default",
            "selfLink": "/api/v1/namespaces/default/services/router",
            "uid": "fabd2440-e3d8-11e6-951c-0e3dd518cefa",
            "resourceVersion": "3206",
            "creationTimestamp": "2017-01-26T15:06:14Z",
            "labels": {
                "router": "router"
            }
        },
        "spec": {
            "ports": [
                {
                    "name": "80-tcp",
                    "protocol": "TCP",
                    "port": 80,
                    "targetPort": 80
                },
                {
                    "name": "443-tcp",
                    "protocol": "TCP",
                    "port": 443,
                    "targetPort": 443
                },
                {
                    "name": "1936-tcp",
                    "protocol": "TCP",
                    "port": 1936,
                    "targetPort": 1936
                },
                {
                    "name": "5000-tcp",
                    "protocol": "TCP",
                    "port": 5000,
                    "targetPort": 5000
                }
            ],
            "selector": {
                "router": "router"
            },
            "clusterIP": "172.30.129.161",
            "type": "ClusterIP",
            "sessionAffinity": "None"
        },
        "status": {
            "loadBalancer": {}
        }
    }'''
    mock_run_cmd.side_effect = [
        (1, '', 'Error from server: services "router" not found'),
        (1, '', 'Error from server: services "router" not found'),
        (0, service, ''),
        (0, service, '')
    ]

    results = CLASS_UNDER_TEST.run_ansible(params, False)

    assert results['changed']
    assert results['results']['returncode'] == 0
    assert results['results']['results'][0]['metadata']['name'] == 'router'
