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
