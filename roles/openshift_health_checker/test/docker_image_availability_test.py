import pytest

from openshift_checks.docker_image_availability import DockerImageAvailability


@pytest.mark.parametrize('deployment_type,is_active', [
    ("origin", True),
    ("openshift-enterprise", True),
    ("enterprise", False),
    ("online", False),
    ("invalid", False),
    ("", False),
])
def test_is_active(deployment_type, is_active):
    task_vars = dict(
        openshift_deployment_type=deployment_type,
    )
    assert DockerImageAvailability.is_active(task_vars=task_vars) == is_active


@pytest.mark.parametrize("is_containerized", [
    True,
    False,
])
def test_all_images_available_locally(is_containerized):
    def execute_module(module_name, args, task_vars):
        assert module_name == "docker_image_facts"
        assert 'name' in args
        assert args['name']
        return {
            'images': [args['name']],
        }

    result = DockerImageAvailability(execute_module=execute_module).run(tmp=None, task_vars=dict(
        openshift=dict(common=dict(
            service_type='origin',
            is_containerized=is_containerized,
        )),
        openshift_deployment_type='origin',
        openshift_release='v3.4',
        openshift_image_tag='3.4',
    ))

    assert not result.get('failed', False)


@pytest.mark.parametrize("module_failure", [
    True,
    False,
])
def test_all_images_available_remotely(module_failure):
    def execute_module(module_name, args, task_vars):
        return {
            'docker_image_facts': {'images': [], 'failed': module_failure},
            'docker_info': {'info': {'Registries': [{'Name': 'docker.io'}, {'Name': 'registry.access.redhat.com'}]}},
        }.get(module_name, {'changed': False})

    result = DockerImageAvailability(execute_module=execute_module).run(tmp=None, task_vars=dict(
        openshift=dict(common=dict(
            service_type='origin',
            is_containerized=False,
        )),
        openshift_deployment_type='origin',
        openshift_release='3.4'
    ))

    assert not result.get('failed', False)


def test_all_images_unavailable():
    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        if module_name == "docker_info":
            return {
                'info': {
                    'Registries': [
                        {
                            'Name': 'docker.io'
                        },
                        {
                            'Name': 'registry.access.redhat.com'
                        }
                    ]
                }
            }

        if module_name == "docker_container":
            return {
                'failed': True,
            }

        return {
            'changed': False,
        }

    check = DockerImageAvailability(execute_module=execute_module)
    actual = check.run(tmp=None, task_vars=dict(
        openshift=dict(common=dict(
            service_type='origin',
            is_containerized=False,
        )),
        openshift_deployment_type="openshift-enterprise",
        openshift_release=None,
    ))

    assert actual['failed']
    assert "required images are not available" in actual['msg']


@pytest.mark.parametrize("message,extra_words", [
    (
        "docker image update failure",
        ["docker image update failure"],
    ),
    (
        "Error connecting: Error while fetching server API version",
        ["Docker is not running"]
    ),
    (
        "Failed to import docker-py",
        ["docker-py module is not installed", "install the python docker-py package"]
    )
])
def test_skopeo_update_failure(message, extra_words):
    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        if module_name == "docker_image":
            return {
                "failed": True,
                "msg": message,
                "changed": False,
            }

        return {
            'changed': False,
        }

    actual = DockerImageAvailability(execute_module=execute_module).run(tmp=None, task_vars=dict(
        openshift=dict(common=dict(
            service_type='origin',
            is_containerized=False,
        )),
        openshift_deployment_type="openshift-enterprise",
        openshift_release='',
    ))

    assert actual["failed"]
    for word in extra_words:
        assert word in actual["msg"]


@pytest.mark.parametrize("module_failure", [
    True,
    False,
])
def test_no_registries_available(module_failure):
    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        if module_name == "docker_info":
            return {
                'changed': False,
                'failed': module_failure,
                'info': {
                    'Registries': [],
                }
            }

        return {
            'changed': False,
        }

    actual = DockerImageAvailability(execute_module=execute_module).run(tmp=None, task_vars=dict(
        openshift=dict(common=dict(
            service_type='origin',
            is_containerized=False,
        )),
        openshift_deployment_type="openshift-enterprise",
        openshift_release='',
    ))

    assert actual['failed']
    assert "docker registries" in actual['msg']
