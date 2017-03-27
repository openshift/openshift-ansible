from openshift_checks.package_update import PackageUpdate


def test_package_update():
    return_value = object()

    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        assert module_name == 'check_yum_update'
        assert 'packages' in module_args
        # empty list of packages means "generic check if 'yum update' will work"
        assert module_args['packages'] == []
        return return_value

    check = PackageUpdate(execute_module=execute_module)
    result = check.run(tmp=None, task_vars=None)
    assert result is return_value
