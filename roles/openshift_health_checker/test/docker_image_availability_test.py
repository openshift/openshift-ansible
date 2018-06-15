import pytest

from openshift_checks.docker_image_availability import DockerImageAvailability, DEPLOYMENT_IMAGE_INFO


@pytest.fixture()
def task_vars():
    return dict(
        openshift_is_atomic=False,
        openshift_service_type='origin',
        openshift_deployment_type='origin',
        openshift_image_tag='',
        group_names=['oo_nodes_to_config', 'oo_masters_to_config'],
    )


@pytest.mark.parametrize('deployment_type, openshift_is_atomic, group_names, expect_active', [
    ("invalid", True, [], False),
    ("", True, [], False),
    ("origin", False, [], False),
    ("openshift-enterprise", False, [], False),
    ("origin", False, ["oo_nodes_to_config", "oo_masters_to_config"], True),
    ("openshift-enterprise", False, ["oo_etcd_to_config"], False),
    ("origin", True, ["nfs"], False),
    ("openshift-enterprise", True, ["lb"], False),
])
def test_is_active(task_vars, deployment_type, openshift_is_atomic, group_names, expect_active):
    task_vars['openshift_deployment_type'] = deployment_type
    task_vars['openshift_is_atomic'] = openshift_is_atomic
    task_vars['group_names'] = group_names
    assert DockerImageAvailability(None, task_vars).is_active() == expect_active


@pytest.mark.parametrize("openshift_is_atomic", [
    True,
    False,
    True,
    False,
])
def test_all_images_available_locally(task_vars, openshift_is_atomic):
    def execute_module(module_name, module_args, *_):
        if module_name == "yum":
            return {}

        assert module_name == "docker_image_facts"
        assert 'name' in module_args
        assert module_args['name']
        return {
            'images': [module_args['name']],
        }

    task_vars['openshift_is_atomic'] = openshift_is_atomic
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
    assert "required container images are not available" in actual['msg']


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
            {"test.reg": False, "docker.io": False},
        ),
        (
            "spam/eggs:v1", ["test.reg"],
            False, True,
            False,
            {"test.reg": True, "docker.io": True},
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

    tv = task_vars()
    tv.update({"openshift_docker_additional_registries": registries})
    check = DockerImageAvailability(execute_module, tv)
    check._module_retry_interval = 0

    available = check.is_available_skopeo_image(image)
    assert available == expect_success
    assert expect_registries_reached == check.reachable_registries


@pytest.mark.parametrize("deployment_type, openshift_is_atomic, groups, oreg_url, expected", [
    (  # standard set of stuff required on nodes
        "origin", False, ['oo_nodes_to_config'], "docker.io/openshift/origin-${component}:${version}",
        set([
            'docker.io/openshift/origin-pod:vtest',
            'docker.io/openshift/origin-deployer:vtest',
            'docker.io/openshift/origin-docker-registry:vtest',
            'docker.io/openshift/origin-haproxy-router:vtest',
            'docker.io/cockpit/kubernetes:latest',  # origin version of registry-console
        ])
    ),
    (  # set a different URL for images
        "origin", False, ['oo_nodes_to_config'], 'foo.io/openshift/origin-${component}:${version}',
        set([
            'foo.io/openshift/origin-pod:vtest',
            'foo.io/openshift/origin-deployer:vtest',
            'foo.io/openshift/origin-docker-registry:vtest',
            'foo.io/openshift/origin-haproxy-router:vtest',
            'docker.io/cockpit/kubernetes:latest',  # AFAICS this is not built from the URL
        ])
    ),
    (
        "origin", True, ['oo_nodes_to_config', 'oo_masters_to_config', 'oo_etcd_to_config'], "docker.io/openshift/origin-${component}:${version}",
        set([
            # images running on top of openshift
            'docker.io/openshift/origin-pod:vtest',
            'docker.io/openshift/origin-deployer:vtest',
            'docker.io/openshift/origin-docker-registry:vtest',
            'docker.io/openshift/origin-haproxy-router:vtest',
            'docker.io/cockpit/kubernetes:latest',
            # containerized component images
            'registry.access.redhat.com/openshift3/ose-node:vtest',
        ])
    ),
    (  # enterprise images
        "openshift-enterprise", True, ['oo_nodes_to_config'], 'foo.io/openshift3/ose-${component}:f13ac45',
        set([
            'foo.io/openshift3/ose-pod:f13ac45',
            'foo.io/openshift3/ose-deployer:f13ac45',
            'foo.io/openshift3/ose-docker-registry:f13ac45',
            'foo.io/openshift3/ose-haproxy-router:f13ac45',
            # registry-console is not constructed/versioned the same as the others.
            'registry.access.redhat.com/openshift3/registry-console:vtest',
            # containerized images aren't built from oreg_url
            'registry.access.redhat.com/openshift3/ose-node:vtest',
        ])
    ),

])
def test_required_images(deployment_type, openshift_is_atomic, groups, oreg_url, expected):
    task_vars = dict(
        openshift_is_atomic=openshift_is_atomic,
        openshift_deployment_type=deployment_type,
        group_names=groups,
        oreg_url=oreg_url,
        openshift_image_tag='vtest',
        osn_image='registry.access.redhat.com/openshift3/ose-node:vtest',
    )

    assert expected == DockerImageAvailability(task_vars=task_vars).required_images()


@pytest.mark.parametrize("task_vars, expected", [
    (
        dict(
            openshift_deployment_type="origin",
            openshift_image_tag="vtest",
        ),
        "docker.io/cockpit/kubernetes:latest",
    ), (
        dict(
            openshift_deployment_type="openshift-enterprise",
            openshift_image_tag="vtest",
        ),
        "registry.access.redhat.com/openshift3/registry-console:vtest",
    ), (
        dict(
            openshift_deployment_type="openshift-enterprise",
            openshift_image_tag="v3.7.0-alpha.0",
            openshift_cockpit_deployer_prefix="registry.example.com/spam/",
        ),
        "registry.example.com/spam/registry-console:v3.7",
    ), (
        dict(
            openshift_deployment_type="origin",
            openshift_image_tag="v3.7.0-alpha.0",
            openshift_cockpit_deployer_prefix="registry.example.com/eggs/",
            openshift_cockpit_deployer_version="spam",
        ),
        "registry.example.com/eggs/kubernetes:spam",
    ),
])
def test_registry_console_image(task_vars, expected):
    info = DEPLOYMENT_IMAGE_INFO[task_vars["openshift_deployment_type"]]
    tag = task_vars["openshift_image_tag"]
    assert expected == DockerImageAvailability(task_vars=task_vars)._registry_console_image(tag, info)


@pytest.mark.parametrize("task_vars, expected", [
    (
        dict(
            group_names=['oo_nodes_to_config'],
            openshift_image_tag="veggs",
            osn_image="registry.access.redhat.com/openshift3/ose-node:vtest",
        ),
        set([
            'registry.access.redhat.com/openshift3/ose-node:vtest', 'docker.io/cockpit/kubernetes:latest',
            'docker.io/openshift/origin-haproxy-router:veggs', 'docker.io/openshift/origin-deployer:veggs',
            'docker.io/openshift/origin-docker-registry:veggs', 'docker.io/openshift/origin-pod:veggs',
        ]),
    ), (
        dict(
            group_names=['oo_masters_to_config'],
        ),
        set(),
    ),
])
def test_containerized(task_vars, expected):
    task_vars.update(dict(
        openshift_is_atomic=True,
        oreg_url="docker.io/openshift/origin-${component}:${version}",
        openshift_deployment_type="origin",
    ))

    assert expected == DockerImageAvailability(task_vars=task_vars).required_images()
