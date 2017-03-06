import base64
import pytest
import testinfra.utils.ansible_runner
import uuid
import yaml

testinfra_hosts = testinfra.utils.ansible_runner.AnsibleRunner(
    '.molecule/ansible_inventory.yml').get_hosts('test_group')


@pytest.fixture()
def namespace(Command, tmpdir):
    namespace = 'test-' + str(uuid.uuid4())

    Command.run_test("mkdir -p {}".format(tmpdir))
    Command.run_test("cp /etc/origin/master/admin.kubeconfig {}/admin.kubeconfig".format(tmpdir))
    Command.run_test("oc new-project {} --config {}/admin.kubeconfig".format(namespace, tmpdir))

    yield namespace

    Command.run_test("oc delete project {} --config {}/admin.kubeconfig".format(namespace, tmpdir))
    Command.run_test("rm -rf {}".format(tmpdir))


@pytest.fixture()
def test_config_file():
    return {
        'name': 'config.yml',
        'contents': yaml.dump({'value': True})
    }


@pytest.fixture()
def test_passwd_file():
    return {
        'name': 'passwords',
        'contents': "test1\ntest2\ntest3\ntest4"
    }


@pytest.fixture()
def secret(namespace, tmpdir, Ansible, test_config_file, test_passwd_file):
    secret_name = 'test-{}'.format(uuid.uuid4())

    config_file = tmpdir.join(test_config_file['name'])
    with config_file.open(mode='w') as f:
        f.write(test_config_file['contents'])

    passwd_file = tmpdir.join(test_passwd_file['name'])
    with passwd_file.open(mode='w') as f:
        f.write(test_passwd_file['contents'])

    Ansible('file', {'dest': str(tmpdir), 'state': 'directory'}, check=False)
    Ansible('copy', {'src': str(config_file), 'dest': str(config_file)}, check=False)
    Ansible('copy', {'src': str(passwd_file), 'dest': str(passwd_file)}, check=False)

    secret_create_params = {
        'name': secret_name,
        'namespace': namespace,
        'state': 'present',
        'files': [
            {
                'name': 'config.yml',
                'path': str(config_file)
            },
            {
                'name': 'passwords',
                'path': str(passwd_file)
            }
        ]
    }
    secret_create = Ansible('oc_secret', secret_create_params, check=False)
    assert secret_create['changed'] is True
    assert secret_create['results']['returncode'] == 0

    yield secret_create_params

    secret_delete_params = {
        'name': secret_name,
        'namespace': namespace,
        'state': 'absent'
    }
    secret_delete = Ansible('oc_secret', secret_delete_params, check=False)
    assert secret_delete['changed'] is True
    assert secret_delete['results']['returncode'] == 0

    Ansible('file', {'dest': str(tmpdir), 'state': 'absent'}, check=False)


def test_decode(secret, Ansible, test_config_file, test_passwd_file):
    secret_list_params = {
        'name': secret['name'],
        'namespace': secret['namespace'],
        'decode': 'yes',
        'state': 'list'
    }
    secret_list = Ansible('oc_secret', secret_list_params)
    assert secret_list['changed'] is False
    assert secret_list['results']['exists'] is True
    assert 'decoded' in secret_list['results']
    assert test_config_file['name'] in secret_list['results']['decoded']
    assert test_passwd_file['name'] in secret_list['results']['decoded']
    assert len(secret_list['results']['decoded']) == 2
    assert secret_list['results']['decoded'][test_config_file['name']] == test_config_file['contents']
    assert secret_list['results']['decoded'][test_passwd_file['name']] == test_passwd_file['contents']


def test_delete_after(tmpdir, namespace, Ansible, test_config_file, test_passwd_file, File):
    secret_name = 'test-{}'.format(uuid.uuid4())

    config_file = tmpdir.join(test_config_file['name'])
    with config_file.open(mode='w') as f:
        f.write(test_config_file['contents'])

    passwd_file = tmpdir.join(test_passwd_file['name'])
    with passwd_file.open(mode='w') as f:
        f.write(test_passwd_file['contents'])

    Ansible('file', {'dest': str(tmpdir), 'state': 'directory'}, check=False)
    Ansible('copy', {'src': str(config_file), 'dest': str(config_file)}, check=False)
    Ansible('copy', {'src': str(passwd_file), 'dest': str(passwd_file)}, check=False)

    secret_create_params = {
        'name': secret_name,
        'namespace': namespace,
        'state': 'present',
        'delete_after': 'yes',
        'files': [
            {
                'name': 'config.yml',
                'path': str(config_file)
            },
            {
                'name': 'passwords',
                'path': str(passwd_file)
            }
        ]
    }
    secret_create = Ansible('oc_secret', secret_create_params, check=False)
    assert secret_create['changed'] is True
    assert secret_create['results']['returncode'] == 0
    assert not File(str(config_file)).exists
    assert not File(str(passwd_file)).exists


@pytest.mark.skip(msg="Need to find a way to test force arg for oc_secret")
def test_force():
    assert False


@pytest.mark.skip(msg="Need to find a way to test kubeconfig arg for oc_secret")
def test_kubeconfig(tmpdir, Ansible, Command, namespace):
    assert False


def test_modify_secret(secret, Ansible, test_config_file, test_passwd_file, tmpdir):
    secret_list_params = {
        'name': secret['name'],
        'namespace': secret['namespace'],
        'state': 'list'
    }
    secret_list = Ansible('oc_secret', secret_list_params)
    assert secret_list['changed'] is False
    assert secret_list['results']['returncode'] == 0
    assert secret_list['results']['exists'] is True
    assert secret_list['results']['results'][0]['type'] == 'Opaque'
    assert secret_list['results']['results'][0]['metadata']['name'] == secret_list_params['name']
    assert secret_list['results']['results'][0]['metadata']['namespace'] == secret_list_params['namespace']
    assert test_config_file['name'] in secret_list['results']['results'][0]['data']
    assert test_passwd_file['name'] in secret_list['results']['results'][0]['data']
    assert len(secret_list['results']['results'][0]['data']) == 2
    assert secret_list['results']['results'][0]['data'][test_config_file['name']] == base64.encodestring(test_config_file['contents']).strip()
    assert secret_list['results']['results'][0]['data'][test_passwd_file['name']] == base64.encodestring(test_passwd_file['contents']).strip()

    config_file_update_params = {
        'name': secret['name'],
        'namespace': secret['namespace'],
        'state': 'present',
        'contents': [
            {
                'path': test_config_file['name'],
                'data': yaml.dump({'value': False})
            }
        ]
    }
    config_file_update = Ansible('oc_secret', config_file_update_params, check=False)
    assert config_file_update['changed'] is True
    assert config_file_update['results']['returncode'] == 0

    secret_list_params = {
        'name': secret['name'],
        'namespace': secret['namespace'],
        'state': 'list'
    }
    secret_list = Ansible('oc_secret', secret_list_params)
    print(yaml.dump(secret_list))
    assert secret_list['changed'] is False
    assert secret_list['results']['returncode'] == 0
    assert secret_list['results']['exists'] is True
    assert secret_list['results']['results'][0]['type'] == 'Opaque'
    assert secret_list['results']['results'][0]['metadata']['name'] == config_file_update_params['name']
    assert secret_list['results']['results'][0]['metadata']['namespace'] == config_file_update_params['namespace']
    assert test_config_file['name'] in secret_list['results']['results'][0]['data']
    assert test_passwd_file['name'] not in secret_list['results']['results'][0]['data']
    assert len(secret_list['results']['results'][0]['data']) == 1
    assert secret_list['results']['results'][0]['data'][test_config_file['name']] == base64.encodestring(config_file_update_params['contents'][0]['data']).strip()


def test_secret_update_check(secret, Ansible, test_config_file, test_passwd_file):
    config_file_update_params = {
        'name': secret['name'],
        'namespace': secret['namespace'],
        'state': 'present',
        'contents': [
            {
                'path': test_config_file['name'],
                'data': yaml.dump({'value': False})
            }
        ]
    }
    config_file_update = Ansible('oc_secret', config_file_update_params)
    assert config_file_update['changed'] is True

    secret_list_params = {
        'name': secret['name'],
        'namespace': secret['namespace'],
        'state': 'list'
    }
    secret_list = Ansible('oc_secret', secret_list_params)
    assert secret_list['changed'] is False
    assert secret_list['results']['returncode'] == 0
    assert secret_list['results']['exists'] is True
    assert secret_list['results']['results'][0]['type'] == 'Opaque'
    assert secret_list['results']['results'][0]['metadata']['name'] == secret_list_params['name']
    assert secret_list['results']['results'][0]['metadata']['namespace'] == secret_list_params['namespace']
    assert test_config_file['name'] in secret_list['results']['results'][0]['data']
    assert test_passwd_file['name'] in secret_list['results']['results'][0]['data']
    assert len(secret_list['results']['results'][0]['data']) == 2
    assert secret_list['results']['results'][0]['data'][test_config_file['name']] == base64.encodestring(test_config_file['contents']).strip()
    assert secret_list['results']['results'][0]['data'][test_passwd_file['name']] == base64.encodestring(test_passwd_file['contents']).strip()


def test_secret_create_check(namespace, Ansible):
    secret_name = 'test-{}'.format(uuid.uuid4())
    secret_create_params = {
        'name': secret_name,
        'namespace': namespace,
        'state': 'present',
        'files': [
            {
                'name': 'my_file',
                'path': 'my/file/path'
            }
        ]
    }
    secret_create = Ansible('oc_secret', secret_create_params)
    assert secret_create['changed'] is True

    secret_list_params = {
        'name': secret_name,
        'namespace': namespace,
        'state': 'list'
    }
    secret_list = Ansible('oc_secret', secret_list_params)
    assert secret_list['changed'] is False
    assert secret_list['results']['exists'] is False


def test_secret_delete_check(secret, Ansible):
    secret_delete_params = {
        'name': secret['name'],
        'namespace': secret['namespace'],
        'state': 'absent'
    }
    secret_delete = Ansible('oc_secret', secret_delete_params)
    assert secret_delete['changed'] is True
    assert secret_delete['msg'] == 'Would have performed a delete.'

    secret_list_params = {
        'name': secret['name'],
        'namespace': secret['namespace'],
        'state': 'list'
    }
    secret_list = Ansible('oc_secret', secret_list_params)
    assert secret_list['changed'] is False
    assert secret_list['results']['returncode'] == 0
    assert secret_list['results']['exists'] is True


def test_secret_already_exists(secret, Ansible, test_config_file, test_passwd_file):
    secret_list_params = {
        'name': secret['name'],
        'namespace': secret['namespace'],
        'state': 'list'
    }
    secret_list = Ansible('oc_secret', secret_list_params)
    assert secret_list['changed'] is False
    assert secret_list['results']['returncode'] == 0
    assert secret_list['results']['exists'] is True
    assert secret_list['results']['results'][0]['type'] == 'Opaque'
    assert secret_list['results']['results'][0]['metadata']['name'] == secret_list_params['name']
    assert secret_list['results']['results'][0]['metadata']['namespace'] == secret_list_params['namespace']
    assert test_config_file['name'] in secret_list['results']['results'][0]['data']
    assert test_passwd_file['name'] in secret_list['results']['results'][0]['data']
    assert len(secret_list['results']['results'][0]['data']) == 2
    assert secret_list['results']['results'][0]['data'][test_config_file['name']] == base64.encodestring(test_config_file['contents']).strip()
    assert secret_list['results']['results'][0]['data'][test_passwd_file['name']] == base64.encodestring(test_passwd_file['contents']).strip()

    secret_create = Ansible('oc_secret', secret, check=False)
    assert secret_create['changed'] is False


def test_secret_exists_not(namespace, Ansible):
    exists_not_name = "exists-not-{}".format(str(uuid.uuid4()))
    secret_params = {
        'name': exists_not_name,
        'namespace': namespace,
        'state': 'absent'
    }
    result = Ansible('oc_secret', secret_params)
    assert result['changed'] is False

    secret_list_params = {
        'name': exists_not_name,
        'namespace': namespace,
        'state': 'list'
    }
    secret_list = Ansible('oc_secret', secret_list_params)
    assert secret_list['changed'] is False
    assert secret_list['results']['exists'] is False
