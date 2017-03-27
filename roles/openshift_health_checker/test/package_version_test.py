from openshift_checks.package_version import PackageVersion


def test_package_version():
    task_vars = dict(
        openshift=dict(common=dict(service_type='origin')),
        openshift_release='v3.5',
    )
    return_value = object()

    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        assert module_name == 'aos_version'
        assert 'prefix' in module_args
        assert 'version' in module_args
        assert module_args['prefix'] == task_vars['openshift']['common']['service_type']
        assert module_args['version'] == task_vars['openshift_release']
        return return_value

    check = PackageVersion(execute_module=execute_module)
    result = check.run(tmp=None, task_vars=task_vars)
    assert result is return_value
