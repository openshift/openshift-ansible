import testinfra.utils.ansible_runner
import os

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_hosts('openshift_excluder_disable')

# scenario-hostname
ansible_vars = testinfra.utils.ansible_runner.AnsibleRunner(
    os.environ['MOLECULE_INVENTORY_FILE']).get_variables('openshift_excluder_disable-disable_excluder')


def test_docker_excluder(Package, Command):
    # skip test if the docker excluder is not enabled
    keys = ["enable_excluders", "enable_docker_excluder", "r_openshift_excluder_enable_excluders", "r_openshift_excluder_enable_docker_excluder"]
    for key in keys:
        if key in ansible_vars and not ansible_vars[key]:
            # check docker excluder is not installed
            p = Package('atomic-openshift-docker-excluder')
            assert not p.is_installed
            return

    # check docker excluder is installed
    p = Package('atomic-openshift-docker-excluder')
    assert p.is_installed

    # check docker excluder is excluding
    cmd = Command.run_test("atomic-openshift-docker-excluder status")
    assert cmd.exit_status == 0


def test_openshift_excluder(Package, Command):
    # check openshift excluder is installed
    keys = ["enable_excluders", "enable_openshift_excluder", "r_openshift_excluder_enable_excluders", "r_openshift_excluder_enable_openshift_excluder"]
    for key in keys:
        if key in ansible_vars and not ansible_vars[key]:
            # check docker excluder is not installed
            p = Package('atomic-openshift-excluder')
            assert not p.is_installed
            return

    # check openshift excluder is installed
    p = Package('atomic-openshift-excluder')
    assert p.is_installed

    # check docker excluder is excluding
    cmd = Command.run_test("atomic-openshift-excluder status")
    assert cmd.exit_status == 1
