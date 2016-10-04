# TODO: Temporarily disabled due to importing old code into openshift-ansible
# repo. We will work on these over time.
# pylint: disable=bad-continuation,missing-docstring,no-self-use,invalid-name,no-value-for-parameter,too-many-lines

import os
import re
import sys
import logging
import click
from pkg_resources import parse_version
from ooinstall import openshift_ansible
from ooinstall.oo_config import OOConfig
from ooinstall.oo_config import OOConfigInvalidHostError
from ooinstall.oo_config import Host, Role
from ooinstall.variants import find_variant, get_variant_version_combos

installer_log = logging.getLogger('installer')
installer_log.setLevel(logging.CRITICAL)
installer_file_handler = logging.FileHandler('/tmp/installer.txt')
installer_file_handler.setFormatter(
    logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
# Example output:
#   2016-08-23 07:34:58,480 - installer - DEBUG - Going to 'load_system_facts'
installer_file_handler.setLevel(logging.DEBUG)
installer_log.addHandler(installer_file_handler)

DEFAULT_ANSIBLE_CONFIG = '/usr/share/atomic-openshift-utils/ansible.cfg'
QUIET_ANSIBLE_CONFIG = '/usr/share/atomic-openshift-utils/ansible-quiet.cfg'
DEFAULT_PLAYBOOK_DIR = '/usr/share/ansible/openshift-ansible/'

UPGRADE_MAPPINGS = {
    '3.0': {
        'minor_version': '3.0',
        'minor_playbook': 'v3_0_minor/upgrade.yml',
        'major_version': '3.1',
        'major_playbook': 'v3_0_to_v3_1/upgrade.yml',
    },
    '3.1': {
        'minor_version': '3.1',
        'minor_playbook': 'v3_1_minor/upgrade.yml',
        'major_playbook': 'v3_1_to_v3_2/upgrade.yml',
        'major_version': '3.2',
    },
    '3.2': {
        'minor_version': '3.2',
        'minor_playbook': 'v3_2/upgrade.yml',
        'major_playbook': 'v3_2/upgrade.yml',
        'major_version': '3.3',
    }
}


def validate_ansible_dir(path):
    if not path:
        raise click.BadParameter('An Ansible path must be provided')
    return path
    # if not os.path.exists(path)):
    #     raise click.BadParameter("Path \"{}\" doesn't exist".format(path))


def is_valid_hostname(hostname):
    if not hostname or len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1]  # strip exactly one dot from the right, if present
    allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))


def validate_prompt_hostname(hostname):
    if hostname == '' or is_valid_hostname(hostname):
        return hostname
    raise click.BadParameter('Invalid hostname. Please double-check this value and re-enter it.')


def get_ansible_ssh_user():
    click.clear()
    message = """
This installation process involves connecting to remote hosts via ssh. Any
account may be used. However, if a non-root account is used, then it must have
passwordless sudo access.
"""
    click.echo(message)
    return click.prompt('User for ssh access', default='root')


def get_master_routingconfig_subdomain():
    click.clear()
    message = """
You might want to override the default subdomain used for exposed routes. If you don't know what this is, use the default value.
"""
    click.echo(message)
    return click.prompt('New default subdomain (ENTER for none)', default='')


def list_hosts(hosts):
    hosts_idx = range(len(hosts))
    for idx in hosts_idx:
        click.echo('   {}: {}'.format(idx, hosts[idx]))


def collect_hosts(oo_cfg, existing_env=False, masters_set=False, print_summary=True):
    """
        Collect host information from user. This will later be filled in using
        Ansible.

        Returns: a list of host information collected from the user
    """
    click.clear()
    click.echo('*** Host Configuration ***')
    message = """
You must now specify the hosts that will compose your OpenShift cluster.

Please enter an IP address or hostname to connect to for each system in the
cluster. You will then be prompted to identify what role you want this system to
serve in the cluster.

OpenShift masters serve the API and web console and coordinate the jobs to run
across the environment. Optionally, you can specify multiple master systems for
a high-availability (HA) deployment. If you choose an HA deployment, then you
are prompted to identify a *separate* system to act as the load balancer for
your cluster once you define all masters and nodes.

If only one master is specified, an etcd instance is embedded within the
OpenShift master service to use as the datastore. This can be later replaced
with a separate etcd instance, if required. If multiple masters are specified,
then a separate etcd cluster is configured with each master serving as a member.

Any masters configured as part of this installation process are also
configured as nodes. This enables the master to proxy to pods
from the API. By default, this node is unschedulable, but this can be changed
after installation with the 'oadm manage-node' command.

OpenShift nodes provide the runtime environments for containers. They host the
required services to be managed by the master.

http://docs.openshift.com/enterprise/latest/architecture/infrastructure_components/kubernetes_infrastructure.html#master
http://docs.openshift.com/enterprise/latest/architecture/infrastructure_components/kubernetes_infrastructure.html#node
    """
    click.echo(message)

    hosts = []
    roles = set(['master', 'node', 'storage', 'etcd'])
    more_hosts = True
    num_masters = 0
    while more_hosts:
        host_props = {}
        host_props['roles'] = []
        host_props['connect_to'] = click.prompt('Enter hostname or IP address',
                                                value_proc=validate_prompt_hostname)

        if not masters_set:
            if click.confirm('Will this host be an OpenShift master?'):
                host_props['roles'].append('master')
                host_props['roles'].append('etcd')
                num_masters += 1

                if oo_cfg.settings['variant_version'] == '3.0':
                    masters_set = True
        host_props['roles'].append('node')

        host_props['containerized'] = False
        if oo_cfg.settings['variant_version'] != '3.0':
            rpm_or_container = \
                click.prompt('Will this host be RPM or Container based (rpm/container)?',
                             type=click.Choice(['rpm', 'container']),
                             default='rpm')
            if rpm_or_container == 'container':
                host_props['containerized'] = True

        host_props['new_host'] = existing_env

        host = Host(**host_props)

        hosts.append(host)

        if print_summary:
            print_installation_summary(hosts, oo_cfg.settings['variant_version'])

        # If we have one master, this is enough for an all-in-one deployment,
        # thus we can start asking if you want to proceed. Otherwise we assume
        # you must.
        if masters_set or num_masters != 2:
            more_hosts = click.confirm('Do you want to add additional hosts?')

    if num_masters >= 3:
        collect_master_lb(hosts)
        roles.add('master_lb')

    if not existing_env:
        collect_storage_host(hosts)

    return hosts, roles


def print_installation_summary(hosts, version=None):
    """
    Displays a summary of all hosts configured thus far, and what role each
    will play.

    Shows total nodes/masters, hints for performing/modifying the deployment
    with additional setup, warnings for invalid or sub-optimal configurations.
    """
    click.clear()
    click.echo('*** Installation Summary ***\n')
    click.echo('Hosts:')
    for host in hosts:
        print_host_summary(hosts, host)

    masters = [host for host in hosts if host.is_master()]
    nodes = [host for host in hosts if host.is_node()]
    dedicated_nodes = [host for host in hosts if host.is_node() and not host.is_master()]
    click.echo('')
    click.echo('Total OpenShift masters: %s' % len(masters))
    click.echo('Total OpenShift nodes: %s' % len(nodes))

    if len(masters) == 1 and version != '3.0':
        ha_hint_message = """
NOTE: Add a total of 3 or more masters to perform an HA installation."""
        click.echo(ha_hint_message)
    elif len(masters) == 2:
        min_masters_message = """
WARNING: A minimum of 3 masters are required to perform an HA installation.
Please add one more to proceed."""
        click.echo(min_masters_message)
    elif len(masters) >= 3:
        ha_message = """
NOTE: Multiple masters specified, this will be an HA deployment with a separate
etcd cluster. You will be prompted to provide the FQDN of a load balancer and
a host for storage once finished entering hosts.
"""
        click.echo(ha_message)

        dedicated_nodes_message = """
WARNING: Dedicated nodes are recommended for an HA deployment. If no dedicated
nodes are specified, each configured master will be marked as a schedulable
node."""

        min_ha_nodes_message = """
WARNING: A minimum of 3 dedicated nodes are recommended for an HA
deployment."""
        if len(dedicated_nodes) == 0:
            click.echo(dedicated_nodes_message)
        elif len(dedicated_nodes) < 3:
            click.echo(min_ha_nodes_message)

    click.echo('')


def print_host_summary(all_hosts, host):
    click.echo("- %s" % host.connect_to)
    if host.is_master():
        click.echo("  - OpenShift master")
    if host.is_node():
        if host.is_dedicated_node():
            click.echo("  - OpenShift node (Dedicated)")
        elif host.is_schedulable_node(all_hosts):
            click.echo("  - OpenShift node")
        else:
            click.echo("  - OpenShift node (Unscheduled)")
    if host.is_master_lb():
        if host.preconfigured:
            click.echo("  - Load Balancer (Preconfigured)")
        else:
            click.echo("  - Load Balancer (HAProxy)")
    if host.is_master():
        if host.is_etcd_member(all_hosts):
            click.echo("  - Etcd Member")
        else:
            click.echo("  - Etcd (Embedded)")
    if host.is_storage():
        click.echo("  - Storage")


def collect_master_lb(hosts):
    """
    Get a valid load balancer from the user and append it to the list of
    hosts.

    Ensure user does not specify a system already used as a master/node as
    this is an invalid configuration.
    """
    message = """
Setting up high-availability masters requires a load balancing solution.
Please provide the FQDN of a host that will be configured as a proxy. This
can be either an existing load balancer configured to balance all masters on
port 8443 or a new host that will have HAProxy installed on it.

If the host provided is not yet configured, a reference HAProxy load
balancer will be installed. It's important to note that while the rest of the
environment will be fault-tolerant, this reference load balancer will not be.
It can be replaced post-installation with a load balancer with the same
hostname.
"""
    click.echo(message)
    host_props = {}

    # Using an embedded function here so we have access to the hosts list:
    def validate_prompt_lb(hostname):
        # Run the standard hostname check first:
        hostname = validate_prompt_hostname(hostname)

        # Make sure this host wasn't already specified:
        for host in hosts:
            if host.connect_to == hostname and (host.is_master() or host.is_node()):
                raise click.BadParameter('Cannot re-use "%s" as a load balancer, '
                                         'please specify a separate host' % hostname)
        return hostname

    host_props['connect_to'] = click.prompt('Enter hostname or IP address',
                                            value_proc=validate_prompt_lb)
    install_haproxy = \
        click.confirm('Should the reference HAProxy load balancer be installed on this host?')
    host_props['preconfigured'] = not install_haproxy
    host_props['roles'] = ['master_lb']
    master_lb = Host(**host_props)
    hosts.append(master_lb)


def collect_storage_host(hosts):
    """
    Get a valid host for storage from the user and append it to the list of
    hosts.
    """
    message = """
Setting up high-availability masters requires a storage host. Please provide a
host that will be configured as a Registry Storage.

Note: Containerized storage hosts are not currently supported.
"""
    click.echo(message)
    host_props = {}

    first_master = next(host for host in hosts if host.is_master())

    hostname_or_ip = click.prompt('Enter hostname or IP address',
                                  value_proc=validate_prompt_hostname,
                                  default=first_master.connect_to)
    existing, existing_host = is_host_already_node_or_master(hostname_or_ip, hosts)
    if existing and existing_host.is_node():
        existing_host.roles.append('storage')
    else:
        host_props['connect_to'] = hostname_or_ip
        host_props['preconfigured'] = False
        host_props['roles'] = ['storage']
        storage = Host(**host_props)
        hosts.append(storage)


def is_host_already_node_or_master(hostname, hosts):
    is_existing = False
    existing_host = None

    for host in hosts:
        if host.connect_to == hostname and (host.is_master() or host.is_node()):
            is_existing = True
            existing_host = host

    return is_existing, existing_host


def confirm_hosts_facts(oo_cfg, callback_facts):
    hosts = oo_cfg.deployment.hosts
    click.clear()
    message = """
The following is a list of the facts gathered from the provided hosts. The
hostname for a system inside the cluster is often different from the hostname
that is resolveable from command-line or web clients, therefore these settings
cannot be validated automatically.

For some cloud providers, the installer is able to gather metadata exposed in
the instance, so reasonable defaults will be provided.

Please confirm that they are correct before moving forward.

"""
    notes = """
Format:

connect_to,IP,public IP,hostname,public hostname

Notes:
 * The installation host is the hostname from the installer's perspective.
 * The IP of the host should be the internal IP of the instance.
 * The public IP should be the externally accessible IP associated with the instance
 * The hostname should resolve to the internal IP from the instances
   themselves.
 * The public hostname should resolve to the external IP from hosts outside of
   the cloud.
"""

    # For testing purposes we need to click.echo only once, so build up
    # the message:
    output = message

    default_facts_lines = []
    default_facts = {}
    for h in hosts:
        if h.preconfigured:
            continue
        try:
            default_facts[h.connect_to] = {}
            h.ip = callback_facts[h.connect_to]["common"]["ip"]
            h.public_ip = callback_facts[h.connect_to]["common"]["public_ip"]
            h.hostname = callback_facts[h.connect_to]["common"]["hostname"]
            h.public_hostname = callback_facts[h.connect_to]["common"]["public_hostname"]
        except KeyError:
            click.echo("Problem fetching facts from {}".format(h.connect_to))
            continue

        default_facts_lines.append(",".join([h.connect_to,
                                             h.ip,
                                             h.public_ip,
                                             h.hostname,
                                             h.public_hostname]))
        output = "%s\n%s" % (output, ",".join([h.connect_to,
                             h.ip,
                             h.public_ip,
                             h.hostname,
                             h.public_hostname]))

    output = "%s\n%s" % (output, notes)
    click.echo(output)
    facts_confirmed = click.confirm("Do the above facts look correct?")
    if not facts_confirmed:
        message = """
Edit %s with the desired values and run `atomic-openshift-installer --unattended install` to restart the install.
""" % oo_cfg.config_path
        click.echo(message)
        # Make sure we actually write out the config file.
        oo_cfg.save_to_disk()
        sys.exit(0)
    return default_facts


def check_hosts_config(oo_cfg, unattended):
    click.clear()
    masters = [host for host in oo_cfg.deployment.hosts if host.is_master()]

    if len(masters) == 2:
        click.echo("A minimum of 3 masters are required for HA deployments.")
        sys.exit(1)

    if len(masters) > 1:
        master_lb = [host for host in oo_cfg.deployment.hosts if host.is_master_lb()]

        if len(master_lb) > 1:
            click.echo('ERROR: More than one master load balancer specified. Only one is allowed.')
            sys.exit(1)
        elif len(master_lb) == 1:
            if master_lb[0].is_master() or master_lb[0].is_node():
                click.echo('ERROR: The master load balancer is configured as a master or node. '
                           'Please correct this.')
                sys.exit(1)
        else:
            message = """
ERROR: No master load balancer specified in config. You must provide the FQDN
of a load balancer to balance the API (port 8443) on all master hosts.

https://docs.openshift.org/latest/install_config/install/advanced_install.html#multiple-masters
"""
            click.echo(message)
            sys.exit(1)

    dedicated_nodes = [host for host in oo_cfg.deployment.hosts
                       if host.is_node() and not host.is_master()]
    if len(dedicated_nodes) == 0:
        message = """
WARNING: No dedicated nodes specified. By default, colocated masters have
their nodes set to unschedulable.  If you proceed all nodes will be labelled
as schedulable.
"""
        if unattended:
            click.echo(message)
        else:
            confirm_continue(message)

    return


def get_variant_and_version(multi_master=False):
    message = "\nWhich variant would you like to install?\n\n"

    i = 1
    combos = get_variant_version_combos()
    for (variant, version) in combos:
        message = "%s\n(%s) %s" % (message, i, variant.description)
        i = i + 1
    message = "%s\n" % message

    click.echo(message)
    if multi_master:
        click.echo('NOTE: 3.0 installations are not')
    response = click.prompt("Choose a variant from above: ", default=1)
    product, version = combos[response - 1]

    return product, version


def confirm_continue(message):
    if message:
        click.echo(message)
    click.confirm("Are you ready to continue?", default=False, abort=True)
    return


def error_if_missing_info(oo_cfg):
    missing_info = False
    if not oo_cfg.deployment.hosts:
        missing_info = True
        click.echo('For unattended installs, hosts must be specified on the '
                   'command line or in the config file: %s' % oo_cfg.config_path)
        sys.exit(1)

    if 'ansible_ssh_user' not in oo_cfg.deployment.variables:
        click.echo("Must specify ansible_ssh_user in configuration file.")
        sys.exit(1)

    # Lookup a variant based on the key we were given:
    if not oo_cfg.settings['variant']:
        click.echo("No variant specified in configuration file.")
        sys.exit(1)

    ver = None
    if 'variant_version' in oo_cfg.settings:
        ver = oo_cfg.settings['variant_version']
    variant, version = find_variant(oo_cfg.settings['variant'], version=ver)
    if variant is None or version is None:
        err_variant_name = oo_cfg.settings['variant']
        if ver:
            err_variant_name = "%s %s" % (err_variant_name, ver)
        click.echo("%s is not an installable variant." % err_variant_name)
        sys.exit(1)
    oo_cfg.settings['variant_version'] = version.name

    # check that all listed host roles are included
    listed_roles = get_host_roles_set(oo_cfg)
    configured_roles = set([role for role in oo_cfg.deployment.roles])
    if listed_roles != configured_roles:
        missing_info = True
        click.echo('Any roles assigned to hosts must be defined.')

    if missing_info:
        sys.exit(1)


def get_host_roles_set(oo_cfg):
    roles_set = set()
    for host in oo_cfg.deployment.hosts:
        for role in host.roles:
            roles_set.add(role)

    return roles_set


def get_proxy_hostnames_and_excludes():
    message = """
If a proxy is needed to reach HTTP and HTTPS traffic, please enter the
name below. This proxy will be configured by default for all processes
that need to reach systems outside the cluster. An example proxy value
would be:

    http://proxy.example.com:8080/

More advanced configuration is possible if using Ansible directly:

https://docs.openshift.com/enterprise/latest/install_config/http_proxies.html
"""
    click.echo(message)

    message = "Specify your http proxy ? (ENTER for none)"
    http_proxy_hostname = click.prompt(message, default='')

    # TODO: Fix this prompt message and behavior. 'ENTER' will default
    # to the http_proxy_hostname if one was provided
    message = "Specify your https proxy ? (ENTER for none)"
    https_proxy_hostname = click.prompt(message, default=http_proxy_hostname)

    if http_proxy_hostname or https_proxy_hostname:
        message = """
All hosts in your OpenShift inventory will automatically be added to the NO_PROXY value.
Please provide any additional hosts to be added to NO_PROXY. (ENTER for none)
"""
        proxy_excludes = click.prompt(message, default='')
    else:
        proxy_excludes = ''

    return http_proxy_hostname, https_proxy_hostname, proxy_excludes


def get_missing_info_from_user(oo_cfg):
    """ Prompts the user for any information missing from the given configuration. """
    click.clear()

    message = """
Welcome to the OpenShift Enterprise 3 installation.

Please confirm that following prerequisites have been met:

* All systems where OpenShift will be installed are running Red Hat Enterprise
  Linux 7.
* All systems are properly subscribed to the required OpenShift Enterprise 3
  repositories.
* All systems have run docker-storage-setup (part of the Red Hat docker RPM).
* All systems have working DNS that resolves not only from the perspective of
  the installer, but also from within the cluster.

When the process completes you will have a default configuration for masters
and nodes.  For ongoing environment maintenance it's recommended that the
official Ansible playbooks be used.

For more information on installation prerequisites please see:
https://docs.openshift.com/enterprise/latest/admin_guide/install/prerequisites.html
"""
    confirm_continue(message)
    click.clear()

    if not oo_cfg.deployment.variables.get('ansible_ssh_user', False):
        oo_cfg.deployment.variables['ansible_ssh_user'] = get_ansible_ssh_user()
        click.clear()

    if not oo_cfg.settings.get('variant', ''):
        variant, version = get_variant_and_version()
        oo_cfg.settings['variant'] = variant.name
        oo_cfg.settings['variant_version'] = version.name
        oo_cfg.settings['variant_subtype'] = version.subtype
        click.clear()

    if not oo_cfg.deployment.hosts:
        oo_cfg.deployment.hosts, roles = collect_hosts(oo_cfg)
        set_infra_nodes(oo_cfg.deployment.hosts)

        for role in roles:
            oo_cfg.deployment.roles[role] = Role(name=role, variables={})
        click.clear()

    if 'master_routingconfig_subdomain' not in oo_cfg.deployment.variables:
        oo_cfg.deployment.variables['master_routingconfig_subdomain'] = get_master_routingconfig_subdomain()
        click.clear()

    # Are any proxy vars already presisted?
    proxy_vars = ['proxy_exclude_hosts', 'proxy_https', 'proxy_http']
    # Empty list if NO proxy vars were presisted
    saved_proxy_vars = [pv for pv in proxy_vars
                        if oo_cfg.deployment.variables.get(pv, 'UNSET') is not 'UNSET']

    installer_log.debug("Evaluated proxy settings, found %s presisted values",
                        len(saved_proxy_vars))
    current_version = parse_version(
        oo_cfg.settings.get('variant_version', '0.0'))
    min_version = parse_version('3.2')

    # No proxy vars were saved and we are running a version which
    # recognizes proxy parameters. We must prompt the user for values
    # if this conditional is true.
    if not saved_proxy_vars and current_version >= min_version:
        installer_log.debug("Prompting user to enter proxy values")
        http_proxy, https_proxy, proxy_excludes = get_proxy_hostnames_and_excludes()
        oo_cfg.deployment.variables['proxy_http'] = http_proxy
        oo_cfg.deployment.variables['proxy_https'] = https_proxy
        oo_cfg.deployment.variables['proxy_exclude_hosts'] = proxy_excludes
        click.clear()

    return oo_cfg


def get_role_variable(oo_cfg, role_name, variable_name):
    try:
        target_role = next(role for role in oo_cfg.deployment.roles if role.name is role_name)
        target_variable = target_role.variables[variable_name]
        return target_variable
    except (StopIteration, KeyError):
        return None


def set_role_variable(oo_cfg, role_name, variable_name, variable_value):
    target_role = next(role for role in oo_cfg.deployment.roles if role.name is role_name)
    target_role[variable_name] = variable_value


def collect_new_nodes(oo_cfg):
    click.clear()
    click.echo('*** New Node Configuration ***')
    message = """
Add new nodes here
    """
    click.echo(message)
    new_nodes, _ = collect_hosts(oo_cfg, existing_env=True, masters_set=True, print_summary=False)
    return new_nodes


def get_installed_hosts(hosts, callback_facts):
    installed_hosts = []
    uninstalled_hosts = []
    for host in [h for h in hosts if h.is_master() or h.is_node()]:
        if host.connect_to in callback_facts.keys():
            if is_installed_host(host, callback_facts):
                installed_hosts.append(host)
            else:
                uninstalled_hosts.append(host)
    return installed_hosts, uninstalled_hosts


def is_installed_host(host, callback_facts):
    version_found = 'common' in callback_facts[host.connect_to].keys() and \
                    callback_facts[host.connect_to]['common'].get('version', '') and \
                    callback_facts[host.connect_to]['common'].get('version', '') != 'None'

    return version_found


# pylint: disable=too-many-branches
# This pylint error will be corrected shortly in separate PR.
def get_hosts_to_run_on(oo_cfg, callback_facts, unattended, force, verbose):

    # Copy the list of existing hosts so we can remove any already installed nodes.
    hosts_to_run_on = list(oo_cfg.deployment.hosts)

    # Check if master or nodes already have something installed
    installed_hosts, uninstalled_hosts = get_installed_hosts(oo_cfg.deployment.hosts, callback_facts)
    if len(installed_hosts) > 0:
        click.echo('Installed environment detected.')
        # This check has to happen before we start removing hosts later in this method
        if not force:
            if not unattended:
                click.echo('By default the installer only adds new nodes '
                           'to an installed environment.')
                response = click.prompt('Do you want to (1) only add additional nodes or '
                                        '(2) reinstall the existing hosts '
                                        'potentially erasing any custom changes?',
                                        type=int)
                # TODO: this should be reworked with error handling.
                # Click can certainly do this for us.
                # This should be refactored as soon as we add a 3rd option.
                if response == 1:
                    force = False
                if response == 2:
                    force = True

        # present a message listing already installed hosts and remove hosts if needed
        for host in installed_hosts:
            if host.is_master():
                click.echo("{} is already an OpenShift master".format(host))
                # Masters stay in the list, we need to run against them when adding
                # new nodes.
            elif host.is_node():
                click.echo("{} is already an OpenShift node".format(host))
                # force is only used for reinstalls so we don't want to remove
                # anything.
                if not force:
                    hosts_to_run_on.remove(host)

        # Handle the cases where we know about uninstalled systems
        # TODO: This logic is getting hard to understand.
        # we should revise all this to be cleaner.
        if not force and len(uninstalled_hosts) > 0:
            for uninstalled_host in uninstalled_hosts:
                click.echo("{} is currently uninstalled".format(uninstalled_host))
            # Fall through
            click.echo('\nUninstalled hosts have been detected in your environment. '
                       'Please make sure your environment was installed successfully '
                       'before adding new nodes. If you want a fresh install, use '
                       '`atomic-openshift-installer install --force`')
            sys.exit(1)
        else:
            if unattended:
                if not force:
                    click.echo('Installed environment detected and no additional '
                               'nodes specified: aborting. If you want a fresh install, use '
                               '`atomic-openshift-installer install --force`')
                    sys.exit(1)
            else:
                if not force:
                    new_nodes = collect_new_nodes(oo_cfg)

                    hosts_to_run_on.extend(new_nodes)
                    oo_cfg.deployment.hosts.extend(new_nodes)

                    openshift_ansible.set_config(oo_cfg)
                    click.echo('Gathering information from hosts...')
                    callback_facts, error = openshift_ansible.default_facts(oo_cfg.deployment.hosts, verbose)
                    if error or callback_facts is None:
                        click.echo("There was a problem fetching the required information. See "
                                   "{} for details.".format(oo_cfg.settings['ansible_log_path']))
                        sys.exit(1)
                else:
                    pass  # proceeding as normal should do a clean install

    return hosts_to_run_on, callback_facts


def set_infra_nodes(hosts):
    if all(host.is_master() for host in hosts):
        infra_list = hosts
    else:
        nodes_list = [host for host in hosts if host.is_schedulable_node(hosts)]
        infra_list = nodes_list[:2]

    for host in infra_list:
        host.node_labels = "{'region': 'infra'}"


@click.group()
@click.pass_context
@click.option('--unattended', '-u', is_flag=True, default=False)
@click.option('--configuration', '-c',
              type=click.Path(file_okay=True,
                              dir_okay=False,
                              writable=True,
                              readable=True),
              default=None)
@click.option('--ansible-playbook-directory',
              '-a',
              type=click.Path(exists=True,
                              file_okay=False,
                              dir_okay=True,
                              readable=True),
              # callback=validate_ansible_dir,
              default=DEFAULT_PLAYBOOK_DIR,
              envvar='OO_ANSIBLE_PLAYBOOK_DIRECTORY')
@click.option('--ansible-log-path',
              type=click.Path(file_okay=True,
                              dir_okay=False,
                              writable=True,
                              readable=True),
              default="/tmp/ansible.log")
@click.option('-v', '--verbose',
              is_flag=True, default=False)
@click.option('-d', '--debug',
              help="Enable installer debugging (/tmp/installer.log)",
              is_flag=True, default=False)
@click.help_option('--help', '-h')
# pylint: disable=too-many-arguments
# pylint: disable=line-too-long
# Main CLI entrypoint, not much we can do about too many arguments.
def cli(ctx, unattended, configuration, ansible_playbook_directory, ansible_log_path, verbose, debug):
    """
    atomic-openshift-installer makes the process for installing OSE or AEP
    easier by interactively gathering the data needed to run on each host.
    It can also be run in unattended mode if provided with a configuration file.

    Further reading: https://docs.openshift.com/enterprise/latest/install_config/install/quick_install.html
    """
    if debug:
        # DEFAULT log level threshold is set to CRITICAL (the
        # highest), anything below that (we only use debug/warning
        # presently) is not logged. If '-d' is given though, we'll
        # lower the threshold to debug (almost everything gets through)
        installer_log.setLevel(logging.DEBUG)
        installer_log.debug("Quick Installer debugging initialized")

    ctx.obj = {}
    ctx.obj['unattended'] = unattended
    ctx.obj['configuration'] = configuration
    ctx.obj['ansible_log_path'] = ansible_log_path
    ctx.obj['verbose'] = verbose

    try:
        oo_cfg = OOConfig(ctx.obj['configuration'])
    except OOConfigInvalidHostError as e:
        click.echo(e)
        sys.exit(1)

    # If no playbook dir on the CLI, check the config:
    if not ansible_playbook_directory:
        ansible_playbook_directory = oo_cfg.settings.get('ansible_playbook_directory', '')
    # If still no playbook dir, check for the default location:
    if not ansible_playbook_directory and os.path.exists(DEFAULT_PLAYBOOK_DIR):
        ansible_playbook_directory = DEFAULT_PLAYBOOK_DIR
    validate_ansible_dir(ansible_playbook_directory)
    oo_cfg.settings['ansible_playbook_directory'] = ansible_playbook_directory
    oo_cfg.ansible_playbook_directory = ansible_playbook_directory
    ctx.obj['ansible_playbook_directory'] = ansible_playbook_directory

    if os.path.exists(DEFAULT_ANSIBLE_CONFIG):
        # If we're installed by RPM this file should exist and we can use it as our default:
        oo_cfg.settings['ansible_config'] = DEFAULT_ANSIBLE_CONFIG

    if os.path.exists(QUIET_ANSIBLE_CONFIG):
        oo_cfg.settings['ansible_quiet_config'] = QUIET_ANSIBLE_CONFIG

    oo_cfg.settings['ansible_log_path'] = ctx.obj['ansible_log_path']

    ctx.obj['oo_cfg'] = oo_cfg
    openshift_ansible.set_config(oo_cfg)


@click.command()
@click.pass_context
def uninstall(ctx):
    oo_cfg = ctx.obj['oo_cfg']
    verbose = ctx.obj['verbose']

    if hasattr(oo_cfg, 'deployment'):
        hosts = oo_cfg.deployment.hosts
    elif hasattr(oo_cfg, 'hosts'):
        hosts = oo_cfg.hosts
    else:
        click.echo("No hosts defined in: %s" % oo_cfg.config_path)
        sys.exit(1)

    click.echo("OpenShift will be uninstalled from the following hosts:\n")
    if not ctx.obj['unattended']:
        # Prompt interactively to confirm:
        for host in hosts:
            click.echo("  * %s" % host.connect_to)
        proceed = click.confirm("\nDo you want to proceed?")
        if not proceed:
            click.echo("Uninstall cancelled.")
            sys.exit(0)

    openshift_ansible.run_uninstall_playbook(hosts, verbose)


@click.command()
@click.option('--latest-minor', '-l', is_flag=True, default=False)
@click.option('--next-major', '-n', is_flag=True, default=False)
@click.pass_context
# pylint: disable=too-many-statements
def upgrade(ctx, latest_minor, next_major):
    oo_cfg = ctx.obj['oo_cfg']

    if len(oo_cfg.deployment.hosts) == 0:
        click.echo("No hosts defined in: %s" % oo_cfg.config_path)
        sys.exit(1)

    variant = oo_cfg.settings['variant']
    if find_variant(variant)[0] is None:
        click.echo("%s is not a supported variant for upgrade." % variant)
        sys.exit(0)

    old_version = oo_cfg.settings['variant_version']
    mapping = UPGRADE_MAPPINGS.get(old_version)

    message = """
        This tool will help you upgrade your existing OpenShift installation.
        Currently running: %s %s
"""
    click.echo(message % (variant, old_version))

    # Map the dynamic upgrade options to the playbook to run for each.
    # Index offset by 1.
    # List contains tuples of booleans for (latest_minor, next_major)
    selections = []
    if not (latest_minor or next_major):
        i = 0
        if 'minor_playbook' in mapping:
            click.echo("(%s) Update to latest %s" % (i + 1, old_version))
            selections.append((True, False))
            i += 1
        if 'major_playbook' in mapping:
            click.echo("(%s) Upgrade to next release: %s" % (i + 1, mapping['major_version']))
            selections.append((False, True))
            i += 1

        response = click.prompt("\nChoose an option from above",
                                type=click.Choice(list(map(str, range(1, len(selections) + 1)))))
        latest_minor, next_major = selections[int(response) - 1]

    if next_major:
        if 'major_playbook' not in mapping:
            click.echo("No major upgrade supported for %s %s with this version "
                       "of atomic-openshift-utils." % (variant, old_version))
            sys.exit(0)
        playbook = mapping['major_playbook']
        new_version = mapping['major_version']
        # Update config to reflect the version we're targetting, we'll write
        # to disk once Ansible completes successfully, not before.
        oo_cfg.settings['variant_version'] = new_version
        if oo_cfg.settings['variant'] == 'enterprise':
            oo_cfg.settings['variant'] = 'openshift-enterprise'

    if latest_minor:
        if 'minor_playbook' not in mapping:
            click.echo("No minor upgrade supported for %s %s with this version "
                       "of atomic-openshift-utils." % (variant, old_version))
            sys.exit(0)
        playbook = mapping['minor_playbook']
        new_version = old_version

    click.echo("OpenShift will be upgraded from %s %s to latest %s %s on the following hosts:\n" % (
        variant, old_version, oo_cfg.settings['variant'], new_version))
    for host in oo_cfg.deployment.hosts:
        click.echo("  * %s" % host.connect_to)

    if not ctx.obj['unattended']:
        # Prompt interactively to confirm:
        if not click.confirm("\nDo you want to proceed?"):
            click.echo("Upgrade cancelled.")
            sys.exit(0)

    retcode = openshift_ansible.run_upgrade_playbook(oo_cfg.deployment.hosts,
                                                     playbook,
                                                     ctx.obj['verbose'])
    if retcode > 0:
        click.echo("Errors encountered during upgrade, please check %s." %
                   oo_cfg.settings['ansible_log_path'])
    else:
        oo_cfg.save_to_disk()
        click.echo("Upgrade completed! Rebooting all hosts is recommended.")


@click.command()
@click.option('--force', '-f', is_flag=True, default=False)
@click.option('--gen-inventory', is_flag=True, default=False,
              help="Generate an Ansible inventory file and exit.")
@click.pass_context
def install(ctx, force, gen_inventory):
    oo_cfg = ctx.obj['oo_cfg']
    verbose = ctx.obj['verbose']

    if ctx.obj['unattended']:
        error_if_missing_info(oo_cfg)
    else:
        oo_cfg = get_missing_info_from_user(oo_cfg)

    check_hosts_config(oo_cfg, ctx.obj['unattended'])

    print_installation_summary(oo_cfg.deployment.hosts, oo_cfg.settings.get('variant_version', None))
    click.echo('Gathering information from hosts...')
    callback_facts, error = openshift_ansible.default_facts(oo_cfg.deployment.hosts,
                                                            verbose)

    if error or callback_facts is None:
        click.echo("There was a problem fetching the required information. "
                   "Please see {} for details.".format(oo_cfg.settings['ansible_log_path']))
        sys.exit(1)

    hosts_to_run_on, callback_facts = get_hosts_to_run_on(
        oo_cfg, callback_facts, ctx.obj['unattended'], force, verbose)

    # We already verified this is not the case for unattended installs, so this can
    # only trigger for live CLI users:
    # TODO: if there are *new* nodes and this is a live install, we may need the  user
    # to confirm the settings for new nodes. Look into this once we're distinguishing
    # between new and pre-existing nodes.
    if not ctx.obj['unattended'] and len(oo_cfg.calc_missing_facts()) > 0:
        confirm_hosts_facts(oo_cfg, callback_facts)

    # Write quick installer config file to disk:
    oo_cfg.save_to_disk()

    # Write Ansible inventory file to disk:
    inventory_file = openshift_ansible.generate_inventory(hosts_to_run_on)

    click.echo()
    click.echo('Wrote atomic-openshift-installer config: %s' % oo_cfg.config_path)
    click.echo("Wrote Ansible inventory: %s" % inventory_file)
    click.echo()

    if gen_inventory:
        sys.exit(0)

    click.echo('Ready to run installation process.')
    message = """
If changes are needed please edit the config file above and re-run.
"""
    if not ctx.obj['unattended']:
        confirm_continue(message)

    error = openshift_ansible.run_main_playbook(inventory_file, oo_cfg.deployment.hosts,
                                                hosts_to_run_on, verbose)

    if error:
        # The bootstrap script will print out the log location.
        message = """
An error was detected. After resolving the problem please relaunch the
installation process.
"""
        click.echo(message)
        sys.exit(1)
    else:
        message = """
The installation was successful!

If this is your first time installing please take a look at the Administrator
Guide for advanced options related to routing, storage, authentication, and
more:

http://docs.openshift.com/enterprise/latest/admin_guide/overview.html
"""
        click.echo(message)

cli.add_command(install)
cli.add_command(upgrade)
cli.add_command(uninstall)

if __name__ == '__main__':
    # This is expected behaviour for context passing with click library:
    # pylint: disable=unexpected-keyword-arg
    cli(obj={})
