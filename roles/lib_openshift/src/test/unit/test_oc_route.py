'''
 Unit tests for oc route
'''
import mock

from lib_openshift.library import oc_route

MODULE_UNDER_TEST = oc_route
CLASS_UNDER_TEST = oc_route.OCRoute


def test_list_route(mock_run_cmd):
    ''' Testing getting a route '''

    # Arrange

    # run_ansible input parameters
    params = {
        'kubeconfig': '/etc/origin/master/admin.kubeconfig',
        'state': 'list',
        'debug': False,
        'name': 'test',
        'namespace': 'default',
        'tls_termination': 'passthrough',
        'dest_cacert_path': None,
        'cacert_path': None,
        'cert_path': None,
        'key_path': None,
        'dest_cacert_content': None,
        'cacert_content': None,
        'cert_content': None,
        'key_content': None,
        'service_name': 'testservice',
        'host': 'test.openshift.com',
        'wildcard_policy': None,
        'weight': None,
        'port': None
    }

    route_result = '''{
        "kind": "Route",
        "apiVersion": "v1",
        "metadata": {
            "name": "test",
            "namespace": "default",
            "selfLink": "/oapi/v1/namespaces/default/routes/test",
            "uid": "1b127c67-ecd9-11e6-96eb-0e0d9bdacd26",
            "resourceVersion": "439182",
            "creationTimestamp": "2017-02-07T01:59:48Z"
        },
        "spec": {
            "host": "test.example",
            "to": {
                "kind": "Service",
                "name": "test",
                "weight": 100
            },
            "port": {
                "targetPort": 8443
            },
            "tls": {
                "termination": "passthrough"
            },
            "wildcardPolicy": "None"
        },
        "status": {
            "ingress": [
                {
                    "host": "test.example",
                    "routerName": "router",
                    "conditions": [
                        {
                            "type": "Admitted",
                            "status": "True",
                            "lastTransitionTime": "2017-02-07T01:59:48Z"
                        }
                    ],
                    "wildcardPolicy": "None"
                }
            ]
        }
    }'''

    # Return values of our mocked function call. These get returned once per call.
    mock_run_cmd.side_effect = [
        # First call to mock
        (0, route_result, ''),
    ]

    # Act
    results = CLASS_UNDER_TEST.run_ansible(params, False)

    # Assert
    assert results['changed'] is False
    assert results['state'] == 'list'
    assert results['results'][0]['metadata']['name'] == 'test'

    # Making sure our mock was called as we expected
    mock_run_cmd.assert_has_calls([
        mock.call(['oc', 'get', 'route', 'test', '-o', 'json', '-n', 'default'], None),
    ])


def test_create_route(mocker, mock_run_cmd):
    ''' Testing getting a route '''
    # Arrange
    mock_write = mocker.patch(MODULE_UNDER_TEST.__name__ + '.Yedit._write')

    # run_ansible input parameters
    params = {
        'kubeconfig': '/etc/origin/master/admin.kubeconfig',
        'state': 'present',
        'debug': False,
        'name': 'test',
        'namespace': 'default',
        'tls_termination': 'edge',
        'dest_cacert_path': None,
        'cacert_path': None,
        'cert_path': None,
        'key_path': None,
        'dest_cacert_content': None,
        'cacert_content': 'testing',
        'cert_content': 'testing',
        'key_content': 'testing',
        'service_name': 'testservice',
        'host': 'test.openshift.com',
        'wildcard_policy': None,
        'weight': None,
        'port': None
    }

    route_result = '''{
            "apiVersion": "v1",
            "kind": "Route",
            "metadata": {
                "creationTimestamp": "2017-02-07T20:55:10Z",
                "name": "test",
                "namespace": "default",
                "resourceVersion": "517745",
                "selfLink": "/oapi/v1/namespaces/default/routes/test",
                "uid": "b6f25898-ed77-11e6-9755-0e737db1e63a"
            },
            "spec": {
                "host": "test.openshift.com",
                "tls": {
                    "caCertificate": "testing",
                    "certificate": "testing",
                    "key": "testing",
                    "termination": "edge"
                },
                "to": {
                    "kind": "Service",
                    "name": "testservice",
                    "weight": 100
                },
                "wildcardPolicy": "None"
            },
            "status": {
                "ingress": [
                    {
                        "conditions": [
                            {
                                "lastTransitionTime": "2017-02-07T20:55:10Z",
                                "status": "True",
                                "type": "Admitted"
                            }
                        ],
                        "host": "test.openshift.com",
                        "routerName": "router",
                        "wildcardPolicy": "None"
                    }
                ]
            }
        }'''

    test_route = '''\
kind: Route
spec:
  tls:
caCertificate: testing
termination: edge
certificate: testing
key: testing
  to:
kind: Service
name: testservice
weight: 100
  host: test.openshift.com
  wildcardPolicy: None
apiVersion: v1
metadata:
  namespace: default
  name: test
'''

    # Return values of our mocked function call. These get returned once per call.
    mock_run_cmd.side_effect = [
        # First call to mock
        (1, '', 'Error from server: routes "test" not found'),
        (1, '', 'Error from server: routes "test" not found'),
        (0, 'route "test" created', ''),
        (0, route_result, ''),
    ]

    # Act
    results = CLASS_UNDER_TEST.run_ansible(params, False)

    # Assert
    assert results['changed']
    assert results['state'] == 'present'
    assert results['results']['results'][0]['metadata']['name'] == 'test'

    mock_write.assert_has_calls = [
        # First call to mock
        mock.call('/tmp/test', test_route)
    ]

    # Making sure our mock was called as we expected
    mock_run_cmd.assert_has_calls([
        mock.call(['oc', 'get', 'route', 'test', '-o', 'json', '-n', 'default'], None),
        mock.call(['oc', 'create', '-f', mock.ANY, '-n', 'default'], None),
        mock.call(['oc', 'get', 'route', 'test', '-o', 'json', '-n', 'default'], None),
    ])
