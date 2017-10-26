import testinfra.utils.ansible_runner

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    '.molecule/ansible_inventory').get_hosts('openshift_excluder_upgrade')

ansible_vars = testinfra.utils.ansible_runner.AnsibleRunner(
    '.molecule/ansible_inventory').get_variables('openshift_excluder_upgrade')


def test_docker_excluder(Package, Command):
    p = Package('atomic-openshift-docker-excluder')

    # not installed nor upgraded
    if not ansible_vars["install_enable_docker_excluder"]:
        if not ansible_vars["upgrade_enable_docker_excluder"]:
            assert not p.is_installed
            return

    # installed
    assert p.is_installed
    # check docker excluder is excluding
    cmd = Command.run_test("atomic-openshift-docker-excluder status")
    assert cmd.exit_status == 0

    # upgraded and enabled in 3.5
    if ansible_vars["upgrade_enable_docker_excluder"]:
        assert p.version.startswith(ansible_vars["upgrade_version"])
    # not upgraded
    else:
        assert p.version.startswith(ansible_vars["install_version"])


def test_openshift_excluder(Package, Command):
    p = Package('atomic-openshift-excluder')

    # not installed nor upgraded
    if not ansible_vars["install_enable_openshift_excluder"]:
        if not ansible_vars["upgrade_enable_openshift_excluder"]:
            assert not p.is_installed
            return

    # installed
    assert p.is_installed
    # check docker excluder is excluding
    cmd = Command.run_test("atomic-openshift-excluder status")
    assert cmd.exit_status == 0

    # upgraded and enabled in 3.5
    if ansible_vars["upgrade_enable_openshift_excluder"]:
        assert p.version.startswith(ansible_vars["upgrade_version"])
    # not upgraded
    else:
        assert p.version.startswith(ansible_vars["install_version"])
