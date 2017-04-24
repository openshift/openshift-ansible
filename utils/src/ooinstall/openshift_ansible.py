# pylint: disable=bad-continuation,missing-docstring,no-self-use,invalid-name,global-statement,global-variable-not-assigned

from __future__ import (absolute_import, print_function)

import socket
import subprocess
import sys
import os
import logging
import yaml
from ooinstall.variants import find_variant
from ooinstall.utils import debug_env

installer_log = logging.getLogger('installer')

CFG = None

ROLES_TO_GROUPS_MAP = {
    'master': 'masters',
    'node': 'nodes',
    'etcd': 'etcd',
    'storage': 'nfs',
    'master_lb': 'lb'
}

VARIABLES_MAP = {
    'ansible_ssh_user': 'ansible_ssh_user',
    'deployment_type': 'deployment_type',
    'variant_subtype': 'deployment_subtype',
    'master_routingconfig_subdomain': 'openshift_master_default_subdomain',
    'proxy_http': 'openshift_http_proxy',
    'proxy_https': 'openshift_https_proxy',
    'proxy_exclude_hosts': 'openshift_no_proxy',
}

HOST_VARIABLES_MAP = {
    'ip': 'openshift_ip',
    'public_ip': 'openshift_public_ip',
    'hostname': 'openshift_hostname',
    'public_hostname': 'openshift_public_hostname',
    'containerized': 'containerized',
}


def set_config(cfg):
    global CFG
    CFG = cfg


def generate_inventory(hosts):
    global CFG

    new_nodes = [host for host in hosts if host.is_node() and host.new_host]
    scaleup = len(new_nodes) > 0

    lb = determine_lb_configuration(hosts)

    base_inventory_path = CFG.settings['ansible_inventory_path']
    base_inventory = open(base_inventory_path, 'w')

    write_inventory_children(base_inventory, scaleup)

    write_inventory_vars(base_inventory, lb)

    # write_inventory_hosts
    for role in CFG.deployment.roles:
        # write group block
        group = ROLES_TO_GROUPS_MAP.get(role, role)
        base_inventory.write("\n[{}]\n".format(group))
        # write each host
        group_hosts = [host for host in hosts if role in host.roles]
        for host in group_hosts:
            schedulable = host.is_schedulable_node(hosts)
            write_host(host, role, base_inventory, schedulable)

    if scaleup:
        base_inventory.write('\n[new_nodes]\n')
        for node in new_nodes:
            write_host(node, 'new_nodes', base_inventory)

    base_inventory.close()
    return base_inventory_path


def determine_lb_configuration(hosts):
    lb = next((host for host in hosts if host.is_master_lb()), None)
    if lb:
        if lb.hostname is None:
            lb.hostname = lb.connect_to
            lb.public_hostname = lb.connect_to

    return lb


def write_inventory_children(base_inventory, scaleup):
    global CFG

    base_inventory.write('\n[OSEv3:children]\n')
    for role in CFG.deployment.roles:
        child = ROLES_TO_GROUPS_MAP.get(role, role)
        base_inventory.write('{}\n'.format(child))

    if scaleup:
        base_inventory.write('new_nodes\n')


# pylint: disable=too-many-branches
def write_inventory_vars(base_inventory, lb):
    global CFG
    base_inventory.write('\n[OSEv3:vars]\n')

    for variable, value in CFG.settings.items():
        inventory_var = VARIABLES_MAP.get(variable, None)
        if inventory_var and value:
            base_inventory.write('{}={}\n'.format(inventory_var, value))

    for variable, value in CFG.deployment.variables.items():
        inventory_var = VARIABLES_MAP.get(variable, variable)
        if value:
            base_inventory.write('{}={}\n'.format(inventory_var, value))

    if CFG.deployment.variables['ansible_ssh_user'] != 'root':
        base_inventory.write('ansible_become=yes\n')

    base_inventory.write('openshift_override_hostname_check=true\n')

    if lb is not None:
        base_inventory.write('openshift_master_cluster_method=native\n')
        base_inventory.write("openshift_master_cluster_hostname={}\n".format(lb.hostname))
        base_inventory.write(
            "openshift_master_cluster_public_hostname={}\n".format(lb.public_hostname))

    if CFG.settings.get('variant_version', None) == '3.1':
        # base_inventory.write('openshift_image_tag=v{}\n'.format(CFG.settings.get('variant_version')))
        base_inventory.write('openshift_image_tag=v{}\n'.format('3.1.1.6'))

    write_proxy_settings(base_inventory)

    # Find the correct deployment type for ansible:
    ver = find_variant(CFG.settings['variant'],
                       version=CFG.settings.get('variant_version', None))[1]
    base_inventory.write('deployment_type={}\n'.format(ver.ansible_key))
    if getattr(ver, 'variant_subtype', False):
        base_inventory.write('deployment_subtype={}\n'.format(ver.deployment_subtype))

    if 'OO_INSTALL_ADDITIONAL_REGISTRIES' in os.environ:
        base_inventory.write('openshift_docker_additional_registries={}\n'.format(
            os.environ['OO_INSTALL_ADDITIONAL_REGISTRIES']))
    if 'OO_INSTALL_INSECURE_REGISTRIES' in os.environ:
        base_inventory.write('openshift_docker_insecure_registries={}\n'.format(
            os.environ['OO_INSTALL_INSECURE_REGISTRIES']))
    if 'OO_INSTALL_PUDDLE_REPO' in os.environ:
        # We have to double the '{' here for literals
        base_inventory.write("openshift_additional_repos=[{{'id': 'ose-devel', "
                             "'name': 'ose-devel', "
                             "'baseurl': '{}', "
                             "'enabled': 1, 'gpgcheck': 0}}]\n".format(os.environ['OO_INSTALL_PUDDLE_REPO']))

    for name, role_obj in CFG.deployment.roles.items():
        if role_obj.variables:
            group_name = ROLES_TO_GROUPS_MAP.get(name, name)
            base_inventory.write("\n[{}:vars]\n".format(group_name))
            for variable, value in role_obj.variables.items():
                inventory_var = VARIABLES_MAP.get(variable, variable)
                if value:
                    base_inventory.write('{}={}\n'.format(inventory_var, value))
            base_inventory.write("\n")


def write_proxy_settings(base_inventory):
    try:
        base_inventory.write("openshift_http_proxy={}\n".format(
            CFG.settings['openshift_http_proxy']))
    except KeyError:
        pass
    try:
        base_inventory.write("openshift_https_proxy={}\n".format(
            CFG.settings['openshift_https_proxy']))
    except KeyError:
        pass
    try:
        base_inventory.write("openshift_no_proxy={}\n".format(
            CFG.settings['openshift_no_proxy']))
    except KeyError:
        pass


def write_host(host, role, inventory, schedulable=None):
    global CFG

    if host.preconfigured:
        return

    facts = ''
    for prop in HOST_VARIABLES_MAP:
        if getattr(host, prop):
            facts += ' {}={}'.format(HOST_VARIABLES_MAP.get(prop), getattr(host, prop))

    if host.other_variables:
        for variable, value in host.other_variables.items():
            facts += " {}={}".format(variable, value)

    if host.node_labels and role == 'node':
        facts += ' openshift_node_labels="{}"'.format(host.node_labels)

    # Distinguish between three states, no schedulability specified (use default),
    # explicitly set to True, or explicitly set to False:
    if role != 'node' or schedulable is None:
        pass
    else:
        facts += " openshift_schedulable={}".format(schedulable)

    installer_host = socket.gethostname()
    if installer_host in [host.connect_to, host.hostname, host.public_hostname]:
        facts += ' ansible_connection=local'
        if os.geteuid() != 0:
            no_pwd_sudo = subprocess.call(['sudo', '-n', 'echo', '-n'])
            if no_pwd_sudo == 1:
                print('The atomic-openshift-installer requires sudo access without a password.')
                sys.exit(1)
            facts += ' ansible_become=yes'

    inventory.write('{} {}\n'.format(host.connect_to, facts))


def load_system_facts(inventory_file, os_facts_path, env_vars, verbose=False):
    """
    Retrieves system facts from the remote systems.
    """
    installer_log.debug("Inside load_system_facts")
    installer_log.debug("load_system_facts will run with Ansible/Openshift environment variables:")
    debug_env(env_vars)

    FNULL = open(os.devnull, 'w')
    args = ['ansible-playbook', '-v'] if verbose \
        else ['ansible-playbook']
    args.extend([
        '--inventory-file={}'.format(inventory_file),
        os_facts_path])
    installer_log.debug("Going to subprocess out to ansible now with these args: %s", ' '.join(args))
    installer_log.debug("Subprocess will run with Ansible/Openshift environment variables:")
    debug_env(env_vars)
    status = subprocess.call(args, env=env_vars, stdout=FNULL)
    if status != 0:
        installer_log.debug("Exit status from subprocess was not 0")
        return [], 1

    with open(CFG.settings['ansible_callback_facts_yaml'], 'r') as callback_facts_file:
        installer_log.debug("Going to try to read this file: %s", CFG.settings['ansible_callback_facts_yaml'])
        try:
            callback_facts = yaml.safe_load(callback_facts_file)
        except yaml.YAMLError as exc:
            print("Error in {}".format(CFG.settings['ansible_callback_facts_yaml']), exc)
            print("Try deleting and rerunning the atomic-openshift-installer")
            sys.exit(1)

    return callback_facts, 0


def default_facts(hosts, verbose=False):
    global CFG
    installer_log.debug("Current global CFG vars here: %s", CFG)
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

    installer_log.debug("facts_env: %s", facts_env)
    installer_log.debug("Going to 'load_system_facts' next")
    return load_system_facts(inventory_file, os_facts_path, facts_env, verbose)


def run_main_playbook(inventory_file, hosts, hosts_to_run_on, verbose=False):
    global CFG
    if len(hosts_to_run_on) != len(hosts):
        main_playbook_path = os.path.join(CFG.ansible_playbook_directory,
                                          'playbooks/byo/openshift-node/scaleup.yml')
    else:
        main_playbook_path = os.path.join(CFG.ansible_playbook_directory,
                                          'playbooks/byo/openshift-cluster/config.yml')
    facts_env = os.environ.copy()
    if 'ansible_log_path' in CFG.settings:
        facts_env['ANSIBLE_LOG_PATH'] = CFG.settings['ansible_log_path']

    # override the ansible config for our main playbook run
    if 'ansible_quiet_config' in CFG.settings:
        facts_env['ANSIBLE_CONFIG'] = CFG.settings['ansible_quiet_config']

    return run_ansible(main_playbook_path, inventory_file, facts_env, verbose)


def run_ansible(playbook, inventory, env_vars, verbose=False):
    installer_log.debug("run_ansible will run with Ansible/Openshift environment variables:")
    debug_env(env_vars)

    args = ['ansible-playbook', '-v'] if verbose \
        else ['ansible-playbook']
    args.extend([
        '--inventory-file={}'.format(inventory),
        playbook])
    installer_log.debug("Going to subprocess out to ansible now with these args: %s", ' '.join(args))
    return subprocess.call(args, env=env_vars)


def run_uninstall_playbook(hosts, verbose=False):
    playbook = os.path.join(CFG.settings['ansible_playbook_directory'],
                            'playbooks/adhoc/uninstall.yml')
    inventory_file = generate_inventory(hosts)
    facts_env = os.environ.copy()
    if 'ansible_log_path' in CFG.settings:
        facts_env['ANSIBLE_LOG_PATH'] = CFG.settings['ansible_log_path']
    if 'ansible_config' in CFG.settings:
        facts_env['ANSIBLE_CONFIG'] = CFG.settings['ansible_config']
    # override the ansible config for our main playbook run
    if 'ansible_quiet_config' in CFG.settings:
        facts_env['ANSIBLE_CONFIG'] = CFG.settings['ansible_quiet_config']

    return run_ansible(playbook, inventory_file, facts_env, verbose)


def run_upgrade_playbook(hosts, playbook, verbose=False):
    playbook = os.path.join(CFG.settings['ansible_playbook_directory'],
                            'playbooks/byo/openshift-cluster/upgrades/{}'.format(playbook))

    # TODO: Upgrade inventory for upgrade?
    inventory_file = generate_inventory(hosts)
    facts_env = os.environ.copy()
    if 'ansible_log_path' in CFG.settings:
        facts_env['ANSIBLE_LOG_PATH'] = CFG.settings['ansible_log_path']
    if 'ansible_config' in CFG.settings:
        facts_env['ANSIBLE_CONFIG'] = CFG.settings['ansible_config']
    # override the ansible config for our main playbook run
    if 'ansible_quiet_config' in CFG.settings:
        facts_env['ANSIBLE_CONFIG'] = CFG.settings['ansible_quiet_config']

    return run_ansible(playbook, inventory_file, facts_env, verbose)
