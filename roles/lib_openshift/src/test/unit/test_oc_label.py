'''
 Unit tests for oc label
'''
from lib_openshift.library import oc_label

MODULE_UNDER_TEST = oc_label
CLASS_UNDER_TEST = oc_label.OCLabel


def test_state_list(mock_run_cmd):
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

    mock_run_cmd.side_effect = [
        (0, ns, ''),
    ]

    results = CLASS_UNDER_TEST.run_ansible(params, False)

    assert results['changed'] is False
    assert results['results']['labels'] == [{'storage_pv_quota': 'False'}]


def test_state_present(mock_run_cmd):
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

    mock_run_cmd.side_effect = [
        (0, ns, ''),
        (0, '', ''),
        (0, ns1, ''),
    ]

    results = CLASS_UNDER_TEST.run_ansible(params, False)

    assert results['changed']
    assert results['results']['results']['labels'][0] == {'storage_pv_quota': 'False', 'awesomens': 'testinglabel'}
