# TODO: Temporarily disabled due to importing old code into openshift-ansible
# repo. We will work on these over time.
# pylint: disable=bad-continuation,missing-docstring,no-self-use,invalid-name,global-statement,global-variable-not-assigned

import socket
import subprocess
import sys
import os
import yaml
from ooinstall.variants import find_variant

CFG = None

def set_config(cfg):
    global CFG
    CFG = cfg

def generate_inventory(hosts):
    global CFG

    installer_host = socket.gethostname()
    base_inventory_path = CFG.settings['ansible_inventory_path']
    base_inventory = open(base_inventory_path, 'w')
    base_inventory.write('\n[OSEv3:children]\nmasters\nnodes\n')
    base_inventory.write('\n[OSEv3:vars]\n')
    base_inventory.write('ansible_ssh_user={}\n'.format(CFG.settings['ansible_ssh_user']))
    if CFG.settings['ansible_ssh_user'] != 'root':
        base_inventory.write('ansible_become=true\n')

    # Find the correct deployment type for ansible:
    ver = find_variant(CFG.settings['variant'],
        version=CFG.settings.get('variant_version', None))[1]
    base_inventory.write('deployment_type={}\n'.format(ver.ansible_key))

    if 'OO_INSTALL_DEVEL_REGISTRY' in os.environ:
        base_inventory.write('oreg_url=rcm-img-docker01.build.eng.bos.redhat.com:'
            '5001/openshift3/ose-${component}:${version}\n')
    if 'OO_INSTALL_PUDDLE_REPO_ENABLE' in os.environ:
        base_inventory.write("openshift_additional_repos=[{'id': 'ose-devel', "
            "'name': 'ose-devel', "
            "'baseurl': 'http://buildvm-devops.usersys.redhat.com"
            "/puddle/build/AtomicOpenShift/3.1/latest/RH7-RHAOS-3.1/$basearch/os', "
            "'enabled': 1, 'gpgcheck': 0}]\n")
    if 'OO_INSTALL_STAGE_REGISTRY' in os.environ:
        base_inventory.write('oreg_url=registry.access.stage.redhat.com/openshift3/ose-${component}:${version}\n')

    if any(host.hostname == installer_host or host.public_hostname == installer_host
            for host in hosts):
        no_pwd_sudo = subprocess.call(['sudo', '-v', '--non-interactive'])
        if no_pwd_sudo == 1:
            print 'The atomic-openshift-installer requires sudo access without a password.'
            sys.exit(1)
        base_inventory.write("ansible_connection=local\n")

    base_inventory.write('\n[masters]\n')
    masters = (host for host in hosts if host.master)
    for master in masters:
        write_host(master, base_inventory)
    base_inventory.write('\n[nodes]\n')
    nodes = (host for host in hosts if host.node)
    for node in nodes:
        # TODO: Until the Master can run the SDN itself we have to configure the Masters
        # as Nodes too.
        scheduleable = True
        # If there's only one Node and it's also a Master we want it to be scheduleable:
        if node in masters and len(masters) != 1:
            scheduleable = False
        write_host(node, base_inventory, scheduleable)
    base_inventory.close()
    return base_inventory_path


def write_host(host, inventory, scheduleable=True):
    global CFG
    facts = ''
    if host.ip:
        facts += ' openshift_ip={}'.format(host.ip)
    if host.public_ip:
        facts += ' openshift_public_ip={}'.format(host.public_ip)
    if host.hostname:
        facts += ' openshift_hostname={}'.format(host.hostname)
    if host.public_hostname:
        facts += ' openshift_public_hostname={}'.format(host.public_hostname)
    # TODO: For not write_host is handles both master and nodes.
    # Technically only nodes will ever need this.
    if not scheduleable:
        facts += ' openshift_scheduleable=False'
    inventory.write('{} {}\n'.format(host, facts))


def load_system_facts(inventory_file, os_facts_path, env_vars, verbose=False):
    """
    Retrieves system facts from the remote systems.
    """
    FNULL = open(os.devnull, 'w')
    args = ['ansible-playbook', '-v'] if verbose \
        else ['ansible-playbook']
    args.extend([
        '--inventory-file={}'.format(inventory_file),
        os_facts_path])
    status = subprocess.call(args, env=env_vars, stdout=FNULL)
    if not status == 0:
        return [], 1
    callback_facts_file = open(CFG.settings['ansible_callback_facts_yaml'], 'r')
    callback_facts = yaml.load(callback_facts_file)
    callback_facts_file.close()
    return callback_facts, 0


def default_facts(hosts, verbose=False):
    global CFG
    inventory_file = generate_inventory(hosts)
    os_facts_path = '{}/playbooks/byo/openshift_facts.yml'.format(CFG.ansible_playbook_directory)

    facts_env = os.environ.copy()
    facts_env["OO_INSTALL_CALLBACK_FACTS_YAML"] = CFG.settings['ansible_callback_facts_yaml']
    facts_env["ANSIBLE_CALLBACK_PLUGINS"] = CFG.settings['ansible_plugins_directory']
    if 'ansible_log_path' in CFG.settings:
        facts_env["ANSIBLE_LOG_PATH"] = CFG.settings['ansible_log_path']
    if 'ansible_config' in CFG.settings:
        facts_env['ANSIBLE_CONFIG'] = CFG.settings['ansible_config']
    return load_system_facts(inventory_file, os_facts_path, facts_env, verbose)


def run_main_playbook(hosts, hosts_to_run_on, verbose=False):
    global CFG
    inventory_file = generate_inventory(hosts)
    if len(hosts_to_run_on) != len(hosts):
        main_playbook_path = os.path.join(CFG.ansible_playbook_directory,
                                          'playbooks/common/openshift-cluster/scaleup.yml')
    else:
        main_playbook_path = os.path.join(CFG.ansible_playbook_directory,
                                          'playbooks/byo/config.yml')
    facts_env = os.environ.copy()
    if 'ansible_log_path' in CFG.settings:
        facts_env['ANSIBLE_LOG_PATH'] = CFG.settings['ansible_log_path']
    if 'ansible_config' in CFG.settings:
        facts_env['ANSIBLE_CONFIG'] = CFG.settings['ansible_config']
    return run_ansible(main_playbook_path, inventory_file, facts_env, verbose)


def run_ansible(playbook, inventory, env_vars, verbose=False):
    args = ['ansible-playbook', '-v'] if verbose \
        else ['ansible-playbook']
    args.extend([
        '--inventory-file={}'.format(inventory),
        playbook])
    return subprocess.call(args, env=env_vars)


def run_uninstall_playbook(verbose=False):
    playbook = os.path.join(CFG.settings['ansible_playbook_directory'],
        'playbooks/adhoc/uninstall.yml')
    inventory_file = generate_inventory(CFG.hosts)
    facts_env = os.environ.copy()
    if 'ansible_log_path' in CFG.settings:
        facts_env['ANSIBLE_LOG_PATH'] = CFG.settings['ansible_log_path']
    if 'ansible_config' in CFG.settings:
        facts_env['ANSIBLE_CONFIG'] = CFG.settings['ansible_config']
    return run_ansible(playbook, inventory_file, facts_env, verbose)


def run_upgrade_playbook(verbose=False):
    playbook = os.path.join(CFG.settings['ansible_playbook_directory'],
        'playbooks/adhoc/upgrades/upgrade.yml')
    # TODO: Upgrade inventory for upgrade?
    inventory_file = generate_inventory(CFG.hosts)
    facts_env = os.environ.copy()
    if 'ansible_log_path' in CFG.settings:
        facts_env['ANSIBLE_LOG_PATH'] = CFG.settings['ansible_log_path']
    if 'ansible_config' in CFG.settings:
        facts_env['ANSIBLE_CONFIG'] = CFG.settings['ansible_config']
    return run_ansible(playbook, inventory_file, facts_env, verbose)

