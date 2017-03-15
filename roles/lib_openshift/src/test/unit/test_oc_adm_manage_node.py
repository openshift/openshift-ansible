'''
 Unit tests for oc_adm_manage_node
'''
import json

from lib_openshift.library import oc_adm_manage_node

MODULE_UNDER_TEST = oc_adm_manage_node
CLASS_UNDER_TEST = oc_adm_manage_node.ManageNode


def test_list_pods(mock_run_cmd):
    ''' Testing a get '''
    params = {'node': ['ip-172-31-49-140.ec2.internal'],
              'schedulable': None,
              'selector': None,
              'pod_selector': None,
              'list_pods': True,
              'kubeconfig': '/etc/origin/master/admin.kubeconfig',
              'evacuate': False,
              'grace_period': False,
              'dry_run': False,
              'force': False}

    pod_list = '''{
"metadata": {},
"items": [
    {
        "metadata": {
            "name": "docker-registry-1-xuhik",
            "generateName": "docker-registry-1-",
            "namespace": "default",
            "selfLink": "/api/v1/namespaces/default/pods/docker-registry-1-xuhik",
            "uid": "ae2a25a2-e316-11e6-80eb-0ecdc51fcfc4",
            "resourceVersion": "1501",
            "creationTimestamp": "2017-01-25T15:55:23Z",
            "labels": {
                "deployment": "docker-registry-1",
                "deploymentconfig": "docker-registry",
                "docker-registry": "default"
            },
            "annotations": {
                "openshift.io/deployment-config.latest-version": "1",
                "openshift.io/deployment-config.name": "docker-registry",
                "openshift.io/deployment.name": "docker-registry-1",
                "openshift.io/scc": "restricted"
            }
        },
        "spec": {}
    },
    {
        "metadata": {
            "name": "router-1-kp3m3",
            "generateName": "router-1-",
            "namespace": "default",
            "selfLink": "/api/v1/namespaces/default/pods/router-1-kp3m3",
            "uid": "9e71f4a5-e316-11e6-80eb-0ecdc51fcfc4",
            "resourceVersion": "1456",
            "creationTimestamp": "2017-01-25T15:54:56Z",
            "labels": {
                "deployment": "router-1",
                "deploymentconfig": "router",
                "router": "router"
            },
            "annotations": {
                "openshift.io/deployment-config.latest-version": "1",
                "openshift.io/deployment-config.name": "router",
                "openshift.io/deployment.name": "router-1",
                "openshift.io/scc": "hostnetwork"
            }
        },
        "spec": {}
    }]
}'''

    mock_run_cmd.return_value = (0, pod_list, '')

    results = CLASS_UNDER_TEST.run_ansible(params, False)

    # returned a single node
    assert len(results['results']['nodes']) == 1
    # returned 2 pods
    assert len(results['results']['nodes']['ip-172-31-49-140.ec2.internal']) == 2


def test_schedulable_false(mock_run_cmd):
    ''' Testing a get '''
    params = {'node': ['ip-172-31-49-140.ec2.internal'],
              'schedulable': False,
              'selector': None,
              'pod_selector': None,
              'list_pods': False,
              'kubeconfig': '/etc/origin/master/admin.kubeconfig',
              'evacuate': False,
              'grace_period': False,
              'dry_run': False,
              'force': False}

    node = {
        "apiVersion": "v1",
        "kind": "Node",
        "metadata": {
            "creationTimestamp": "2017-01-26T14:34:43Z",
            "labels": {
                "beta.kubernetes.io/arch": "amd64",
                "beta.kubernetes.io/instance-type": "m4.large",
                "beta.kubernetes.io/os": "linux",
                "failure-domain.beta.kubernetes.io/region": "us-east-1",
                "failure-domain.beta.kubernetes.io/zone": "us-east-1c",
                "hostname": "opstest-node-compute-0daaf",
                "kubernetes.io/hostname": "ip-172-31-51-111.ec2.internal",
                "ops_node": "old",
                "region": "us-east-1",
                "type": "compute"
            },
            "name": "ip-172-31-51-111.ec2.internal",
            "resourceVersion": "6936",
            "selfLink": "/api/v1/nodes/ip-172-31-51-111.ec2.internal",
            "uid": "93d7fdfb-e3d4-11e6-a982-0e84250fc302"
        },
        "spec": {
            "externalID": "i-06bb330e55c699b0f",
            "providerID": "aws:///us-east-1c/i-06bb330e55c699b0f",
        }
    }

    scheduling_result = ("NAME                            STATUS    AGE\n"
                         "ip-172-31-49-140.ec2.internal   Ready,SchedulingDisabled     5h\n")

    mock_run_cmd.side_effect = [
        (0, json.dumps(node), ''),
        (0, scheduling_result, '')
    ]

    results = CLASS_UNDER_TEST.run_ansible(params, False)

    assert results['changed'] is True
    assert results['results']['nodes'][0]['name'] == 'ip-172-31-49-140.ec2.internal'
    assert results['results']['nodes'][0]['schedulable'] is False
