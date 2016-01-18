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
    masters = [host for host in hosts if host.master]
    nodes = [host for host in hosts if host.node]
    new_nodes = [host for host in hosts if host.node and host.new_host]
    proxy = determine_proxy_configuration(hosts)
    multiple_masters = len(masters) > 1
    scaleup = len(new_nodes) > 0

    base_inventory_path = CFG.settings['ansible_inventory_path']
    base_inventory = open(base_inventory_path, 'w')

    write_inventory_children(base_inventory, multiple_masters, proxy, scaleup)

    write_inventory_vars(base_inventory, multiple_masters, proxy)

    # Find the correct deployment type for ansible:
    ver = find_variant(CFG.settings['variant'],
        version=CFG.settings.get('variant_version', None))[1]
    base_inventory.write('deployment_type={}\n'.format(ver.ansible_key))

    if 'OO_INSTALL_ADDITIONAL_REGISTRIES' in os.environ:
        base_inventory.write('cli_docker_additional_registries={}\n'
          .format(os.environ['OO_INSTALL_ADDITIONAL_REGISTRIES']))
    if 'OO_INSTALL_INSECURE_REGISTRIES' in os.environ:
        base_inventory.write('cli_docker_insecure_registries={}\n'
          .format(os.environ['OO_INSTALL_INSECURE_REGISTRIES']))
    if 'OO_INSTALL_PUDDLE_REPO' in os.environ:
        # We have to double the '{' here for literals
        base_inventory.write("openshift_additional_repos=[{{'id': 'ose-devel', "
            "'name': 'ose-devel', "
            "'baseurl': '{}', "
            "'enabled': 1, 'gpgcheck': 0}}]\n".format(os.environ['OO_INSTALL_PUDDLE_REPO']))

    base_inventory.write('\n[masters]\n')
    for master in masters:
        write_host(master, base_inventory)

    if len(masters) > 1:
        base_inventory.write('\n[etcd]\n')
        for master in masters:
            write_host(master, base_inventory)

    base_inventory.write('\n[nodes]\n')

    for node in nodes:
        # Let the fact defaults decide if we're not a master:
        schedulable = None

        # If the node is also a master, we must explicitly set schedulablity:
        if node.master:
            schedulable = node.is_schedulable_node(hosts)
        write_host(node, base_inventory, schedulable)

    if not getattr(proxy, 'preconfigured', True):
        base_inventory.write('\n[lb]\n')
        write_host(proxy, base_inventory)

    if scaleup:
        base_inventory.write('\n[new_nodes]\n')
        for node in new_nodes:
            write_host(node, base_inventory)

    base_inventory.close()
    return base_inventory_path

def determine_proxy_configuration(hosts):
    proxy = next((host for host in hosts if host.master_lb), None)
    if proxy:
        if proxy.hostname == None:
            proxy.hostname = proxy.connect_to
            proxy.public_hostname = proxy.connect_to
        return proxy

    return None

def write_inventory_children(base_inventory, multiple_masters, proxy, scaleup):
    global CFG

    base_inventory.write('\n[OSEv3:children]\n')
    base_inventory.write('masters\n')
    base_inventory.write('nodes\n')
    if scaleup:
        base_inventory.write('new_nodes\n')
    if multiple_masters:
        base_inventory.write('etcd\n')
    if not getattr(proxy, 'preconfigured', True):
        base_inventory.write('lb\n')

def write_inventory_vars(base_inventory, multiple_masters, proxy):
    global CFG
    base_inventory.write('\n[OSEv3:vars]\n')
    base_inventory.write('ansible_ssh_user={}\n'.format(CFG.settings['ansible_ssh_user']))
    if CFG.settings['ansible_ssh_user'] != 'root':
        base_inventory.write('ansible_become=true\n')
    if multiple_masters and proxy is not None:
        base_inventory.write('openshift_master_cluster_method=native\n')
        base_inventory.write("openshift_master_cluster_hostname={}\n".format(proxy.hostname))
        base_inventory.write("openshift_master_cluster_public_hostname={}\n".format(proxy.public_hostname))


def write_host(host, inventory, schedulable=None):
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
    if host.containerized:
        facts += ' containerized={}'.format(host.containerized)
    # TODO: For not write_host is handles both master and nodes.
    # Technically only nodes will ever need this.

    # Distinguish between three states, no schedulability specified (use default),
    # explicitly set to True, or explicitly set to False:
    if schedulable is None:
        pass
    elif schedulable:
        facts += ' openshift_schedulable=True'
    elif not schedulable:
        facts += ' openshift_schedulable=False'

    installer_host = socket.gethostname()
    if installer_host in [host.connect_to, host.hostname, host.public_hostname]:
        facts += ' ansible_connection=local'
        if os.geteuid() != 0:
            no_pwd_sudo = subprocess.call(['sudo', '-n', 'echo', 'openshift'])
            if no_pwd_sudo == 1:
                print 'The atomic-openshift-installer requires sudo access without a password.'
                sys.exit(1)
            facts += ' ansible_become=true'

    inventory.write('{} {}\n'.format(host.connect_to, facts))


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

    with open(CFG.settings['ansible_callback_facts_yaml'], 'r') as callback_facts_file:
        try:
            callback_facts = yaml.safe_load(callback_facts_file)
        except yaml.YAMLError, exc:
            print "Error in {}".format(CFG.settings['ansible_callback_facts_yaml']), exc
            print "Try deleting and rerunning the atomic-openshift-installer"
            sys.exit(1)

    return callback_facts, 0


def default_facts(hosts, verbose=False):
    global CFG
    inventory_file = generate_inventory(hosts)
    os_facts_path = '{}/playbooks/byo/openshift_facts.yml'.format(CFG.ansible_playbook_directory)

    facts_env = os.environ.copy()
    facts_env["OO_INSTALL_CALLBACK_FACTS_YAML"] = CFG.settings['ansible_callback_facts_yaml']
    facts_env["ANSIBLE_CALLBACK_PLUGINS"] = CFG.settings['ansible_plugins_directory']
    facts_env["OPENSHIFT_MASTER_CLUSTER_METHOD"] = 'native'
    if 'ansible_log_path' in CFG.settings:
        facts_env["ANSIBLE_LOG_PATH"] = CFG.settings['ansible_log_path']
    if 'ansible_config' in CFG.settings:
        facts_env['ANSIBLE_CONFIG'] = CFG.settings['ansible_config']
    return load_system_facts(inventory_file, os_facts_path, facts_env, verbose)


def run_main_playbook(hosts, hosts_to_run_on, verbose=False):
    global CFG
    inventory_file = generate_inventory(hosts_to_run_on)
    if len(hosts_to_run_on) != len(hosts):
        main_playbook_path = os.path.join(CFG.ansible_playbook_directory,
                                          'playbooks/byo/openshift-cluster/scaleup.yml')
    else:
        main_playbook_path = os.path.join(CFG.ansible_playbook_directory,
                                          'playbooks/byo/openshift-cluster/config.yml')
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
    # TODO: do not hardcode the upgrade playbook, add ability to select the
    # right playbook depending on the type of upgrade.
    playbook = os.path.join(CFG.settings['ansible_playbook_directory'],
        'playbooks/byo/openshift-cluster/upgrades/v3_0_to_v3_1/upgrade.yml')
    # TODO: Upgrade inventory for upgrade?
    inventory_file = generate_inventory(CFG.hosts)
    facts_env = os.environ.copy()
    if 'ansible_log_path' in CFG.settings:
        facts_env['ANSIBLE_LOG_PATH'] = CFG.settings['ansible_log_path']
    if 'ansible_config' in CFG.settings:
        facts_env['ANSIBLE_CONFIG'] = CFG.settings['ansible_config']
    return run_ansible(playbook, inventory_file, facts_env, verbose)
