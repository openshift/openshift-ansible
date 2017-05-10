import pytest

from openshift_checks.ovs_version import OvsVersion, OpenShiftCheckException


def test_openshift_version_not_supported():
    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        return {}

    openshift_release = '111.7.0'

    task_vars = dict(
        openshift=dict(common=dict(service_type='origin')),
        openshift_release=openshift_release,
        openshift_image_tag='v' + openshift_release,
        openshift_deployment_type='origin',
    )

    check = OvsVersion(execute_module=execute_module)
    with pytest.raises(OpenShiftCheckException) as excinfo:
        check.run(tmp=None, task_vars=task_vars)

    assert "no recommended version of Open vSwitch" in str(excinfo.value)


def test_invalid_openshift_release_format():
    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        return {}

    task_vars = dict(
        openshift=dict(common=dict(service_type='origin')),
        openshift_image_tag='v0',
        openshift_deployment_type='origin',
    )

    check = OvsVersion(execute_module=execute_module)
    with pytest.raises(OpenShiftCheckException) as excinfo:
        check.run(tmp=None, task_vars=task_vars)
    assert "invalid version" in str(excinfo.value)


@pytest.mark.parametrize('openshift_release,expected_ovs_version', [
    ("3.5", "2.6"),
    ("3.6", "2.6"),
    ("3.4", "2.4"),
    ("3.3", "2.4"),
    ("1.0", "2.4"),
])
def test_ovs_package_version(openshift_release, expected_ovs_version):
    task_vars = dict(
        openshift=dict(common=dict(service_type='origin')),
        openshift_release=openshift_release,
        openshift_image_tag='v' + openshift_release,
    )
    return_value = object()

    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        assert module_name == 'rpm_version'
        assert "package_list" in module_args

        for pkg in module_args["package_list"]:
            if pkg["name"] == "openvswitch":
                assert pkg["version"] == expected_ovs_version

        return return_value

    check = OvsVersion(execute_module=execute_module)
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
def test_ovs_version_skip_when_not_master_nor_node(group_names, is_containerized, is_active):
    task_vars = dict(
        group_names=group_names,
        openshift=dict(common=dict(is_containerized=is_containerized)),
    )
    assert OvsVersion.is_active(task_vars=task_vars) == is_active
