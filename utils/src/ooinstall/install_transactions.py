import subprocess
import os
import yaml
from variants import find_variant

CFG = None

def set_config(cfg):
    global CFG
    CFG = cfg

def generate_inventory(hosts):
    print hosts
    global CFG
    base_inventory_path = CFG.settings['ansible_inventory_path']
    base_inventory = open(base_inventory_path, 'w')
    base_inventory.write('\n[OSEv3:children]\nmasters\nnodes\n')
    base_inventory.write('\n[OSEv3:vars]\n')
    base_inventory.write('ansible_ssh_user={}\n'.format(CFG.settings['ansible_ssh_user']))
    if CFG.settings['ansible_ssh_user'] != 'root':
        base_inventory.write('ansible_sudo=true\n')

    # Find the correct deployment type for ansible:
    variant, ver = find_variant(CFG.settings['variant'],
        version=CFG.settings.get('variant_version', None))
    base_inventory.write('deployment_type={}\n'.format(ver.ansible_key))

    if 'OO_INSTALL_DEVEL_REGISTRY' in os.environ:
        base_inventory.write('oreg_url=rcm-img-docker01.build.eng.bos.redhat.com:5001/openshift3/ose-${component}:${version}\n')
    if 'OO_INSTALL_PUDDLE_REPO_ENABLE' in os.environ:
        base_inventory.write("openshift_additional_repos=[{'id': 'ose-devel', 'name': 'ose-devel', 'baseurl': 'http://buildvm-devops.usersys.redhat.com/puddle/build/AtomicOpenShift/3.1/latest/RH7-RHAOS-3.1/$basearch/os', 'enabled': 1, 'gpgcheck': 0}]\n")
    if 'OO_INSTALL_STAGE_REGISTRY' in os.environ:
        base_inventory.write('oreg_url=registry.access.stage.redhat.com/openshift3/ose-${component}:${version}\n')

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


def load_system_facts(inventory_file, os_facts_path, env_vars):
    """
    Retrieves system facts from the remote systems.
    """
    FNULL = open(os.devnull, 'w')
    status = subprocess.call(['ansible-playbook',
                     '--inventory-file={}'.format(inventory_file),
                     os_facts_path],
                     env=env_vars)
                         #                     stdout=FNULL)
    if not status == 0:
        return [], 1
    callback_facts_file = open(CFG.settings['ansible_callback_facts_yaml'], 'r')
    callback_facts = yaml.load(callback_facts_file)
    callback_facts_file.close()
    return callback_facts, 0


def default_facts(hosts):
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
    return load_system_facts(inventory_file, os_facts_path, facts_env)


def run_main_playbook(hosts, hosts_to_run_on):
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
    return run_ansible(main_playbook_path, inventory_file, facts_env)

def run_ansible(playbook, inventory, env_vars):
    return subprocess.call(['ansible-playbook',
                             '--inventory-file={}'.format(inventory),
                             playbook],
                             env=env_vars)
