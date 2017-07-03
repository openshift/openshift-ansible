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
    def execute_module(module_name, module_args, task_vars):
        if module_name == "yum":
            return {"changed": True}

        assert module_name == "docker_image_facts"
        assert 'name' in module_args
        assert module_args['name']
        return {
            'images': [module_args['name']],
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
        openshift_image_tag='3.4',
        group_names=['nodes', 'masters'],
    ))

    assert not result.get('failed', False)


@pytest.mark.parametrize("available_locally", [
    False,
    True,
])
def test_all_images_available_remotely(available_locally):
    def execute_module(module_name, module_args, task_vars):
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
        openshift_image_tag='v3.4',
        group_names=['nodes', 'masters'],
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
        openshift_image_tag='latest',
        group_names=['nodes', 'masters'],
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
        openshift_image_tag='',
        group_names=['nodes', 'masters'],
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
        openshift_image_tag='',
        group_names=['nodes', 'masters'],
    ))

    assert not actual.get("failed", False)


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

    assert expected == DockerImageAvailability("DUMMY").required_images(task_vars)


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
    assert expected == DockerImageAvailability("DUMMY").required_images(task_vars)
