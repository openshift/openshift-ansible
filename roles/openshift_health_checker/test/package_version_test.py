import pytest

from openshift_checks.package_version import PackageVersion


def test_package_version():
    task_vars = dict(
        openshift=dict(common=dict(service_type='origin')),
        openshift_release='3.5',
        openshift_deployment_type='origin',
    )
    return_value = object()

    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        assert module_name == 'aos_version'
        assert 'requested_openshift_release' in module_args
        assert 'openshift_deployment_type' in module_args
        assert 'rpm_prefix' in module_args
        assert module_args['requested_openshift_release'] == task_vars['openshift_release']
        assert module_args['openshift_deployment_type'] == task_vars['openshift_deployment_type']
        assert module_args['rpm_prefix'] == task_vars['openshift']['common']['service_type']
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
