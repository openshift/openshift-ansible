import pytest

from openshift_checks.package_availability import PackageAvailability


@pytest.mark.parametrize('task_vars,must_have_packages,must_not_have_packages', [
    (
        dict(openshift=dict(common=dict(service_type='openshift'))),
        set(),
        set(['openshift-master', 'openshift-node']),
    ),
    (
        dict(
            openshift=dict(common=dict(service_type='origin')),
            group_names=['masters'],
        ),
        set(['origin-master']),
        set(['origin-node']),
    ),
    (
        dict(
            openshift=dict(common=dict(service_type='atomic-openshift')),
            group_names=['nodes'],
        ),
        set(['atomic-openshift-node']),
        set(['atomic-openshift-master']),
    ),
    (
        dict(
            openshift=dict(common=dict(service_type='atomic-openshift')),
            group_names=['masters', 'nodes'],
        ),
        set(['atomic-openshift-master', 'atomic-openshift-node']),
        set(),
    ),
])
def test_package_availability(task_vars, must_have_packages, must_not_have_packages):
    return_value = object()

    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None):
        assert module_name == 'check_yum_update'
        assert 'packages' in module_args
        assert set(module_args['packages']).issuperset(must_have_packages)
        assert not set(module_args['packages']).intersection(must_not_have_packages)
        return return_value

    check = PackageAvailability(execute_module=execute_module)
    result = check.run(tmp=None, task_vars=task_vars)
    assert result is return_value
