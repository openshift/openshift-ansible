import pytest

from openshift_checks.docker_image_availability import DockerImageAvailability


@pytest.mark.parametrize('deployment_type, is_containerized, group_names, expect_active', [
    ("origin", True, [], True),
    ("openshift-enterprise", True, [], True),
    ("enterprise", True, [], False),
    ("online", True, [], False),
    ("invalid", True, [], False),
    ("", True, [], False),
    ("origin", False, [], False),
    ("openshift-enterprise", False, [], False),
    ("origin", False, ["nodes", "masters"], True),
    ("openshift-enterprise", False, ["etcd"], False),
])
def test_is_active(deployment_type, is_containerized, group_names, expect_active):
    task_vars = dict(
        openshift=dict(common=dict(is_containerized=is_containerized)),
        openshift_deployment_type=deployment_type,
        group_names=group_names,
    )
    assert DockerImageAvailability.is_active(task_vars=task_vars) == expect_active


@pytest.mark.parametrize("is_containerized,is_atomic", [
    (True, True),
    (False, False),
    (True, False),
    (False, True),
])
def test_all_images_available_locally(is_containerized, is_atomic):
    def execute_module(module_name, args, task_vars):
        if module_name == "yum":
            return {"changed": True}

        assert module_name == "docker_image_facts"
        assert 'name' in args
        assert args['name']
        return {
            'images': [args['name']],
        }

    result = DockerImageAvailability(execute_module=execute_module).run(tmp=None, task_vars=dict(
        openshift=dict(
            common=dict(
                service_type='origin',
                is_containerized=is_containerized,
                is_atomic=is_atomic,
            ),
            docker=dict(additional_registries=["docker.io"]),
        ),
        openshift_deployment_type='origin',
        openshift_release='v3.4',
        openshift_image_tag='3.4',
    ))

    assert not result.get('failed', False)


@pytest.mark.parametrize("available_locally", [
    False,
    True,
])
def test_all_images_available_remotely(available_locally):
    def execute_module(module_name, args, task_vars):
        if module_name == 'docker_image_facts':
            return {'images': [], 'failed': available_locally}
        return {'changed': False}

    result = DockerImageAvailability(execute_module=execute_module).run(tmp=None, task_vars=dict(
        openshift=dict(
            common=dict(
                service_type='origin',
                is_containerized=False,
                is_atomic=False,
            ),
            docker=dict(additional_registries=["docker.io", "registry.access.redhat.com"]),
        ),
        openshift_deployment_type='origin',
        openshift_release='3.4',
        openshift_image_tag='v3.4',
    ))

    assert not result.get('failed', False)


def test_all_images_unavailable():
    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        if module_name == "command":
            return {
                'failed': True,
            }

        return {
            'changed': False,
        }

    check = DockerImageAvailability(execute_module=execute_module)
    actual = check.run(tmp=None, task_vars=dict(
        openshift=dict(
            common=dict(
                service_type='origin',
                is_containerized=False,
                is_atomic=False,
            ),
            docker=dict(additional_registries=["docker.io"]),
        ),
        openshift_deployment_type="openshift-enterprise",
        openshift_release=None,
        openshift_image_tag='latest'
    ))

    assert actual['failed']
    assert "required Docker images are not available" in actual['msg']


@pytest.mark.parametrize("message,extra_words", [
    (
        "docker image update failure",
        ["docker image update failure"],
    ),
    (
        "No package matching 'skopeo' found available, installed or updated",
        ["dependencies can be installed via `yum`"]
    ),
])
def test_skopeo_update_failure(message, extra_words):
    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        if module_name == "yum":
            return {
                "failed": True,
                "msg": message,
                "changed": False,
            }

        return {'changed': False}

    actual = DockerImageAvailability(execute_module=execute_module).run(tmp=None, task_vars=dict(
        openshift=dict(
            common=dict(
                service_type='origin',
                is_containerized=False,
                is_atomic=False,
            ),
            docker=dict(additional_registries=["unknown.io"]),
        ),
        openshift_deployment_type="openshift-enterprise",
        openshift_release='',
        openshift_image_tag='',
    ))

    assert actual["failed"]
    for word in extra_words:
        assert word in actual["msg"]


@pytest.mark.parametrize("deployment_type,registries", [
    ("origin", ["unknown.io"]),
    ("openshift-enterprise", ["registry.access.redhat.com"]),
    ("openshift-enterprise", []),
])
def test_registry_availability(deployment_type, registries):
    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        return {
            'changed': False,
        }

    actual = DockerImageAvailability(execute_module=execute_module).run(tmp=None, task_vars=dict(
        openshift=dict(
            common=dict(
                service_type='origin',
                is_containerized=False,
                is_atomic=False,
            ),
            docker=dict(additional_registries=registries),
        ),
        openshift_deployment_type=deployment_type,
        openshift_release='',
        openshift_image_tag='',
    ))

    assert not actual.get("failed", False)
