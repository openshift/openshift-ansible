import pytest
import json

from openshift_checks.logging.logging import LoggingCheck, OpenShiftCheckException

task_vars_config_base = dict(openshift=dict(common=dict(config_base='/etc/origin')))


logging_namespace = "logging"


def canned_loggingcheck(exec_oc=None):
    """Create a LoggingCheck object with canned exec_oc method"""
    check = LoggingCheck("dummy")  # fails if a module is actually invoked
    check.logging_namespace = 'logging'
    if exec_oc:
        check.exec_oc = exec_oc
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

plain_kibana_pod = {
    "metadata": {
        "labels": {"component": "kibana", "deploymentconfig": "logging-kibana"},
        "name": "logging-kibana-1",
    },
    "status": {
        "containerStatuses": [{"ready": True}, {"ready": True}],
        "conditions": [{"status": "True", "type": "Ready"}],
    }
}

fluentd_pod_node1 = {
    "metadata": {
        "labels": {"component": "fluentd", "deploymentconfig": "logging-fluentd"},
        "name": "logging-fluentd-1",
    },
    "spec": {"host": "node1", "nodeName": "node1"},
    "status": {
        "containerStatuses": [{"ready": True}],
        "conditions": [{"status": "True", "type": "Ready"}],
    }
}

plain_curator_pod = {
    "metadata": {
        "labels": {"component": "curator", "deploymentconfig": "logging-curator"},
        "name": "logging-curator-1",
    },
    "status": {
        "containerStatuses": [{"ready": True}],
        "conditions": [{"status": "True", "type": "Ready"}],
        "podIP": "10.10.10.10",
    }
}


@pytest.mark.parametrize('problem, expect', [
    ("[Errno 2] No such file or directory", "supposed to be a master"),
    ("Permission denied", "Unexpected error using `oc`"),
])
def test_oc_failure(problem, expect):
    def execute_module(module_name, args, task_vars):
        if module_name == "ocutil":
            return dict(failed=True, result=problem)
        return dict(changed=False)

    check = LoggingCheck({})

    with pytest.raises(OpenShiftCheckException) as excinfo:
        check.exec_oc(execute_module, logging_namespace, 'get foo', [], task_vars=task_vars_config_base)
    assert expect in str(excinfo)


groups_with_first_master = dict(masters=['this-host', 'other-host'])
groups_with_second_master = dict(masters=['other-host', 'this-host'])
groups_not_a_master = dict(masters=['other-host'])


@pytest.mark.parametrize('groups, logging_deployed, is_active', [
    (groups_with_first_master, True, True),
    (groups_with_first_master, False, False),
    (groups_not_a_master, True, False),
    (groups_with_second_master, True, False),
    (groups_not_a_master, True, False),
])
def test_is_active(groups, logging_deployed, is_active):
    task_vars = dict(
        ansible_ssh_host='this-host',
        groups=groups,
        openshift_hosted_logging_deploy=logging_deployed,
    )

    assert LoggingCheck.is_active(task_vars=task_vars) == is_active


@pytest.mark.parametrize('pod_output, expect_pods, expect_error', [
    (
        'No resources found.',
        None,
        'There are no pods in the logging namespace',
    ),
    (
        json.dumps({'items': [plain_kibana_pod, plain_es_pod, plain_curator_pod, fluentd_pod_node1]}),
        [plain_es_pod],
        None,
    ),
])
def test_get_pods_for_component(pod_output, expect_pods, expect_error):
    check = canned_loggingcheck(lambda exec_module, namespace, cmd, args, task_vars: pod_output)
    pods, error = check.get_pods_for_component(
        lambda name, args, task_vars: {},
        logging_namespace,
        "es",
        {}
    )
    assert_error(error, expect_error)
