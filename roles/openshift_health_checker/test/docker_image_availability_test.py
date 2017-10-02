import pytest

from openshift_checks.docker_image_availability import DockerImageAvailability


@pytest.fixture()
def task_vars():
    return dict(
        openshift=dict(
            common=dict(
                service_type='origin',
                is_containerized=False,
                is_atomic=False,
            ),
            docker=dict(),
        ),
        openshift_deployment_type='origin',
        openshift_image_tag='',
        group_names=['nodes', 'masters'],
    )


@pytest.mark.parametrize('deployment_type, is_containerized, group_names, expect_active', [
    ("origin", True, [], True),
    ("openshift-enterprise", True, [], True),
    ("invalid", True, [], False),
    ("", True, [], False),
    ("origin", False, [], False),
    ("openshift-enterprise", False, [], False),
    ("origin", False, ["nodes", "masters"], True),
    ("openshift-enterprise", False, ["etcd"], False),
])
def test_is_active(task_vars, deployment_type, is_containerized, group_names, expect_active):
    task_vars['openshift_deployment_type'] = deployment_type
    task_vars['openshift']['common']['is_containerized'] = is_containerized
    task_vars['group_names'] = group_names
    assert DockerImageAvailability(None, task_vars).is_active() == expect_active


@pytest.mark.parametrize("is_containerized,is_atomic", [
    (True, True),
    (False, False),
    (True, False),
    (False, True),
])
def test_all_images_available_locally(task_vars, is_containerized, is_atomic):
    def execute_module(module_name, module_args, *_):
        if module_name == "yum":
            return {}

        assert module_name == "docker_image_facts"
        assert 'name' in module_args
        assert module_args['name']
        return {
            'images': [module_args['name']],
        }

    task_vars['openshift']['common']['is_containerized'] = is_containerized
    task_vars['openshift']['common']['is_atomic'] = is_atomic
    result = DockerImageAvailability(execute_module, task_vars).run()

    assert not result.get('failed', False)


@pytest.mark.parametrize("available_locally", [
    False,
    True,
])
def test_all_images_available_remotely(task_vars, available_locally):
    def execute_module(module_name, *_):
        if module_name == 'docker_image_facts':
            return {'images': [], 'failed': available_locally}
        return {}

    task_vars['openshift_docker_additional_registries'] = ["docker.io", "registry.access.redhat.com"]
    task_vars['openshift_image_tag'] = 'v3.4'
    check = DockerImageAvailability(execute_module, task_vars)
    check._module_retry_interval = 0
    result = check.run()

    assert not result.get('failed', False)


def test_all_images_unavailable(task_vars):
    def execute_module(module_name=None, *args):
        if module_name == "wait_for":
            return {}
        elif module_name == "command":
            return {'failed': True}

        return {}  # docker_image_facts failure

    task_vars['openshift_docker_additional_registries'] = ["docker.io"]
    task_vars['openshift_deployment_type'] = "openshift-enterprise"
    task_vars['openshift_image_tag'] = 'latest'
    check = DockerImageAvailability(execute_module, task_vars)
    check._module_retry_interval = 0
    actual = check.run()

    assert actual['failed']
    assert "required Docker images are not available" in actual['msg']


def test_no_known_registries():
    def execute_module(module_name=None, *_):
        if module_name == "command":
            return {
                'failed': True,
            }

        return {
            'changed': False,
        }

    def mock_known_docker_registries():
        return []

    dia = DockerImageAvailability(execute_module, task_vars=dict(
        openshift=dict(
            common=dict(
                service_type='origin',
                is_containerized=False,
                is_atomic=False,
            )
        ),
        openshift_docker_additional_registries=["docker.io"],
        openshift_deployment_type="openshift-enterprise",
        openshift_image_tag='latest',
        group_names=['nodes', 'masters'],
    ))
    dia.known_docker_registries = mock_known_docker_registries
    actual = dia.run()
    assert actual['failed']
    assert "Unable to retrieve any docker registries." in actual['msg']


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
def test_skopeo_update_failure(task_vars, message, extra_words):
    def execute_module(module_name=None, *_):
        if module_name == "yum":
            return {
                "failed": True,
                "msg": message,
            }

        return {}

    task_vars['openshift_docker_additional_registries'] = ["unknown.io"]
    task_vars['openshift_deployment_type'] = "openshift-enterprise"
    check = DockerImageAvailability(execute_module, task_vars)
    check._module_retry_interval = 0
    actual = check.run()

    assert actual["failed"]
    for word in extra_words:
        assert word in actual["msg"]


@pytest.mark.parametrize(
    "image, registries, connection_test_failed, skopeo_failed, "
    "expect_success, expect_registries_reached", [
        (
            "spam/eggs:v1", ["test.reg"],
            True, True,
            False,
            {"test.reg": False},
        ),
        (
            "spam/eggs:v1", ["test.reg"],
            False, True,
            False,
            {"test.reg": True},
        ),
        (
            "eggs.reg/spam/eggs:v1", ["test.reg"],
            False, False,
            True,
            {"eggs.reg": True},
        ),
    ])
def test_registry_availability(image, registries, connection_test_failed, skopeo_failed,
                               expect_success, expect_registries_reached):
    def execute_module(module_name=None, *_):
        if module_name == "wait_for":
            return dict(msg="msg", failed=connection_test_failed)
        elif module_name == "command":
            return dict(msg="msg", failed=skopeo_failed)

    check = DockerImageAvailability(execute_module, task_vars())
    check._module_retry_interval = 0

    available = check.is_available_skopeo_image(image, registries)
    assert available == expect_success
    assert expect_registries_reached == check.reachable_registries


@pytest.mark.parametrize("deployment_type, is_containerized, groups, oreg_url, expected", [
    (  # standard set of stuff required on nodes
        "origin", False, ['nodes'], None,
        set([
            'openshift/origin-pod:vtest',
            'openshift/origin-deployer:vtest',
            'openshift/origin-docker-registry:vtest',
            'openshift/origin-haproxy-router:vtest',
            'cockpit/kubernetes',  # origin version of registry-console
        ])
    ),
    (  # set a different URL for images
        "origin", False, ['nodes'], 'foo.io/openshift/origin-${component}:${version}',
        set([
            'foo.io/openshift/origin-pod:vtest',
            'foo.io/openshift/origin-deployer:vtest',
            'foo.io/openshift/origin-docker-registry:vtest',
            'foo.io/openshift/origin-haproxy-router:vtest',
            'cockpit/kubernetes',  # AFAICS this is not built from the URL
        ])
    ),
    (
        "origin", True, ['nodes', 'masters', 'etcd'], None,
        set([
            # images running on top of openshift
            'openshift/origin-pod:vtest',
            'openshift/origin-deployer:vtest',
            'openshift/origin-docker-registry:vtest',
            'openshift/origin-haproxy-router:vtest',
            'cockpit/kubernetes',
            # containerized component images
            'openshift/origin:vtest',
            'openshift/node:vtest',
            'openshift/openvswitch:vtest',
            'registry.access.redhat.com/rhel7/etcd',
        ])
    ),
    (  # enterprise images
        "openshift-enterprise", True, ['nodes'], 'foo.io/openshift3/ose-${component}:f13ac45',
        set([
            'foo.io/openshift3/ose-pod:f13ac45',
            'foo.io/openshift3/ose-deployer:f13ac45',
            'foo.io/openshift3/ose-docker-registry:f13ac45',
            'foo.io/openshift3/ose-haproxy-router:f13ac45',
            # registry-console is not constructed/versioned the same as the others.
            'registry.access.redhat.com/openshift3/registry-console',
            # containerized images aren't built from oreg_url
            'openshift3/node:vtest',
            'openshift3/openvswitch:vtest',
        ])
    ),
    (
        "openshift-enterprise", True, ['etcd', 'lb'], 'foo.io/openshift3/ose-${component}:f13ac45',
        set([
            'registry.access.redhat.com/rhel7/etcd',
            # lb does not yet come in a containerized version
        ])
    ),

])
def test_required_images(deployment_type, is_containerized, groups, oreg_url, expected):
    task_vars = dict(
        openshift=dict(
            common=dict(
                is_containerized=is_containerized,
                is_atomic=False,
            ),
        ),
        openshift_deployment_type=deployment_type,
        group_names=groups,
        oreg_url=oreg_url,
        openshift_image_tag='vtest',
    )

    assert expected == DockerImageAvailability(task_vars=task_vars).required_images()


def test_containerized_etcd():
    task_vars = dict(
        openshift=dict(
            common=dict(
                is_containerized=True,
            ),
        ),
        openshift_deployment_type="origin",
        group_names=['etcd'],
    )
    expected = set(['registry.access.redhat.com/rhel7/etcd'])
    assert expected == DockerImageAvailability(task_vars=task_vars).required_images()
