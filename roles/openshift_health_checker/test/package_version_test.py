import pytest

from openshift_checks.package_version import PackageVersion, OpenShiftCheckException


@pytest.mark.parametrize('openshift_release, extra_words', [
    ('111.7.0', ["no recommended version of Open vSwitch"]),
    ('0.0.0', ["no recommended version of Docker"]),
])
def test_openshift_version_not_supported(openshift_release, extra_words):
    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        return {}

    task_vars = dict(
        openshift=dict(common=dict(service_type='origin')),
        openshift_release=openshift_release,
        openshift_image_tag='v' + openshift_release,
        openshift_deployment_type='origin',
    )

    check = PackageVersion(execute_module=execute_module)
    with pytest.raises(OpenShiftCheckException) as excinfo:
        check.run(tmp=None, task_vars=task_vars)

    for word in extra_words:
        assert word in str(excinfo.value)


def test_invalid_openshift_release_format():
    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        return {}

    task_vars = dict(
        openshift=dict(common=dict(service_type='origin')),
        openshift_image_tag='v0',
        openshift_deployment_type='origin',
    )

    check = PackageVersion(execute_module=execute_module)
    with pytest.raises(OpenShiftCheckException) as excinfo:
        check.run(tmp=None, task_vars=task_vars)
    assert "invalid version" in str(excinfo.value)


@pytest.mark.parametrize('openshift_release', [
    "3.5",
    "3.6",
    "3.4",
    "3.3",
])
def test_package_version(openshift_release):
    task_vars = dict(
        openshift=dict(common=dict(service_type='origin')),
        openshift_release=openshift_release,
        openshift_image_tag='v' + openshift_release,
        openshift_deployment_type='origin',
    )
    return_value = object()

    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        assert module_name == 'aos_version'
        assert "package_list" in module_args

        for pkg in module_args["package_list"]:
            if "-master" in pkg["name"] or "-node" in pkg["name"]:
                assert pkg["version"] == task_vars["openshift_release"]

        return return_value

    check = PackageVersion(execute_module=execute_module)
    result = check.run(tmp=None, task_vars=task_vars)
    assert result is return_value


@pytest.mark.parametrize('deployment_type,openshift_release,expected_ovs_version', [
    ("openshift-enterprise", "3.5", "2.6"),
    ("origin", "3.6", "2.6"),
    ("openshift-enterprise", "3.4", "2.4"),
    ("origin", "3.3", "2.4"),
])
def test_ovs_package_version(deployment_type, openshift_release, expected_ovs_version):
    task_vars = dict(
        openshift=dict(common=dict(service_type='origin')),
        openshift_release=openshift_release,
        openshift_image_tag='v' + openshift_release,
        openshift_deployment_type=deployment_type,
    )
    return_value = object()

    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        assert module_name == 'aos_version'
        assert "package_list" in module_args

        for pkg in module_args["package_list"]:
            if pkg["name"] == "openvswitch":
                assert pkg["version"] == expected_ovs_version

        return return_value

    check = PackageVersion(execute_module=execute_module)
    result = check.run(tmp=None, task_vars=task_vars)
    assert result is return_value


@pytest.mark.parametrize('deployment_type,openshift_release,expected_docker_version', [
    ("origin", "3.5", "1.12"),
    ("openshift-enterprise", "3.4", "1.12"),
    ("origin", "3.3", "1.10"),
    ("openshift-enterprise", "3.2", "1.10"),
    ("origin", "3.1", "1.8"),
    ("openshift-enterprise", "3.1", "1.8"),
])
def test_docker_package_version(deployment_type, openshift_release, expected_docker_version):
    task_vars = dict(
        openshift=dict(common=dict(service_type='origin')),
        openshift_release=openshift_release,
        openshift_image_tag='v' + openshift_release,
        openshift_deployment_type=deployment_type,
    )
    return_value = object()

    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        assert module_name == 'aos_version'
        assert "package_list" in module_args

        for pkg in module_args["package_list"]:
            if pkg["name"] == "docker":
                assert pkg["version"] == expected_docker_version

        return return_value

    check = PackageVersion(execute_module=execute_module)
    result = check.run(tmp=None, task_vars=task_vars)
    assert result is return_value


@pytest.mark.parametrize('group_names,is_containerized,is_active', [
    (['masters'], False, True),
    # ensure check is skipped on containerized installs
    (['masters'], True, False),
    (['nodes'], False, True),
    (['masters', 'nodes'], False, True),
    (['masters', 'etcd'], False, True),
    ([], False, False),
    (['etcd'], False, False),
    (['lb'], False, False),
    (['nfs'], False, False),
])
def test_package_version_skip_when_not_master_nor_node(group_names, is_containerized, is_active):
    task_vars = dict(
        group_names=group_names,
        openshift=dict(common=dict(is_containerized=is_containerized)),
    )
    assert PackageVersion.is_active(task_vars=task_vars) == is_active
