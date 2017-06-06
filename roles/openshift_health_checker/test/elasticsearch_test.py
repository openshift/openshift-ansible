import pytest
import json

from openshift_checks.logging.elasticsearch import Elasticsearch

task_vars_config_base = dict(openshift=dict(common=dict(config_base='/etc/origin')))


def canned_elasticsearch(exec_oc=None):
    """Create an Elasticsearch check object with canned exec_oc method"""
    check = Elasticsearch("dummy")  # fails if a module is actually invoked
    if exec_oc:
        check._exec_oc = exec_oc
    return check


def assert_error(error, expect_error):
    if expect_error:
        assert error
        assert expect_error in error
    else:
        assert not error


plain_es_pod = {
    "metadata": {
        "labels": {"component": "es", "deploymentconfig": "logging-es"},
        "name": "logging-es",
    },
    "status": {
        "conditions": [{"status": "True", "type": "Ready"}],
        "containerStatuses": [{"ready": True}],
        "podIP": "10.10.10.10",
    },
    "_test_master_name_str": "name logging-es",
}

split_es_pod = {
    "metadata": {
        "labels": {"component": "es", "deploymentconfig": "logging-es-2"},
        "name": "logging-es-2",
    },
    "status": {
        "conditions": [{"status": "True", "type": "Ready"}],
        "containerStatuses": [{"ready": True}],
        "podIP": "10.10.10.10",
    },
    "_test_master_name_str": "name logging-es-2",
}


def test_check_elasticsearch():
    assert 'No logging Elasticsearch pods' in canned_elasticsearch().check_elasticsearch([], {})

    # canned oc responses to match so all the checks pass
    def _exec_oc(cmd, args, task_vars):
        if '_cat/master' in cmd:
            return 'name logging-es'
        elif '/_nodes' in cmd:
            return json.dumps(es_node_list)
        elif '_cluster/health' in cmd:
            return '{"status": "green"}'
        elif ' df ' in cmd:
            return 'IUse% Use%\n 3%  4%\n'
        else:
            raise Exception(cmd)

    assert not canned_elasticsearch(_exec_oc).check_elasticsearch([plain_es_pod], {})


def pods_by_name(pods):
    return {pod['metadata']['name']: pod for pod in pods}


@pytest.mark.parametrize('pods, expect_error', [
    (
        [],
        'No logging Elasticsearch masters',
    ),
    (
        [plain_es_pod],
        None,
    ),
    (
        [plain_es_pod, split_es_pod],
        'Found multiple Elasticsearch masters',
    ),
])
def test_check_elasticsearch_masters(pods, expect_error):
    test_pods = list(pods)
    check = canned_elasticsearch(lambda cmd, args, task_vars: test_pods.pop(0)['_test_master_name_str'])

    errors = check._check_elasticsearch_masters(pods_by_name(pods), task_vars_config_base)
    assert_error(''.join(errors), expect_error)


es_node_list = {
    'nodes': {
        'random-es-name': {
            'host': 'logging-es',
        }}}


@pytest.mark.parametrize('pods, node_list, expect_error', [
    (
        [],
        {},
        'No logging Elasticsearch masters',
    ),
    (
        [plain_es_pod],
        es_node_list,
        None,
    ),
    (
        [plain_es_pod],
        {},  # empty list of nodes triggers KeyError
        "Failed to query",
    ),
    (
        [split_es_pod],
        es_node_list,
        'does not correspond to any known ES pod',
    ),
])
def test_check_elasticsearch_node_list(pods, node_list, expect_error):
    check = canned_elasticsearch(lambda cmd, args, task_vars: json.dumps(node_list))

    errors = check._check_elasticsearch_node_list(pods_by_name(pods), task_vars_config_base)
    assert_error(''.join(errors), expect_error)


@pytest.mark.parametrize('pods, health_data, expect_error', [
    (
        [plain_es_pod],
        [{"status": "green"}],
        None,
    ),
    (
        [plain_es_pod],
        [{"no-status": "should bomb"}],
        'Could not retrieve cluster health status',
    ),
    (
        [plain_es_pod, split_es_pod],
        [{"status": "green"}, {"status": "red"}],
        'Elasticsearch cluster health status is RED',
    ),
])
def test_check_elasticsearch_cluster_health(pods, health_data, expect_error):
    test_health_data = list(health_data)
    check = canned_elasticsearch(lambda cmd, args, task_vars: json.dumps(test_health_data.pop(0)))

    errors = check._check_es_cluster_health(pods_by_name(pods), task_vars_config_base)
    assert_error(''.join(errors), expect_error)


@pytest.mark.parametrize('disk_data, expect_error', [
    (
        'df: /elasticsearch/persistent: No such file or directory\n',
        'Could not retrieve storage usage',
    ),
    (
        'IUse% Use%\n 3%  4%\n',
        None,
    ),
    (
        'IUse% Use%\n 95%  40%\n',
        'Inode percent usage on the storage volume',
    ),
    (
        'IUse% Use%\n 3%  94%\n',
        'Disk percent usage on the storage volume',
    ),
])
def test_check_elasticsearch_diskspace(disk_data, expect_error):
    check = canned_elasticsearch(lambda cmd, args, task_vars: disk_data)

    errors = check._check_elasticsearch_diskspace(pods_by_name([plain_es_pod]), task_vars_config_base)
    assert_error(''.join(errors), expect_error)
