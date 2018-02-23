import pytest

from openshift_checks.ovs_version import OvsVersion
from openshift_checks import OpenShiftCheckException


def test_invalid_openshift_release_format():
    def execute_module(*_):
        return {}

    task_vars = dict(
        openshift=dict(common=dict()),
        openshift_image_tag='v0',
        openshift_deployment_type='origin',
        openshift_service_type='origin'
    )

    with pytest.raises(OpenShiftCheckException) as excinfo:
        OvsVersion(execute_module, task_vars).run()
    assert "invalid version" in str(excinfo.value)


@pytest.mark.parametrize('openshift_release,expected_ovs_version', [
    ("3.7", ["2.6", "2.7", "2.8"]),
    ("3.5", ["2.6", "2.7"]),
    ("3.6", ["2.6", "2.7", "2.8"]),
    ("3.4", "2.4"),
    ("3.3", "2.4"),
    ("1.0", "2.4"),
])
def test_ovs_package_version(openshift_release, expected_ovs_version):
    task_vars = dict(
        openshift=dict(common=dict()),
        openshift_release=openshift_release,
        openshift_image_tag='v' + openshift_release,
        openshift_service_type='origin'
    )
    return_value = {}  # note: check.execute_module modifies return hash contents

    def execute_module(module_name=None, module_args=None, *_):
        assert module_name == 'rpm_version'
        assert "package_list" in module_args

        for pkg in module_args["package_list"]:
            if pkg["name"] == "openvswitch":
                assert pkg["version"] == expected_ovs_version

        return return_value

    check = OvsVersion(execute_module, task_vars)
    check.openshift_to_ovs_version = {
        (3, 4): "2.4",
        (3, 5): ["2.6", "2.7"],
        (3, 6): ["2.6", "2.7", "2.8"],
    }
    result = check.run()
    assert result is return_value


@pytest.mark.parametrize('group_names,openshift_is_containerized,is_active', [
    (['oo_masters_to_config'], False, True),
    # ensure check is skipped on containerized installs
    (['oo_masters_to_config'], True, False),
    (['oo_nodes_to_config'], False, True),
    (['oo_masters_to_config', 'oo_nodes_to_config'], False, True),
    (['oo_masters_to_config', 'oo_etcd_to_config'], False, True),
    ([], False, False),
    (['oo_etcd_to_config'], False, False),
    (['lb'], False, False),
    (['nfs'], False, False),
])
def test_ovs_version_skip_when_not_master_nor_node(group_names, openshift_is_containerized, is_active):
    task_vars = dict(
        group_names=group_names,
        openshift_is_containerized=openshift_is_containerized,
    )
    assert OvsVersion(None, task_vars).is_active() == is_active
