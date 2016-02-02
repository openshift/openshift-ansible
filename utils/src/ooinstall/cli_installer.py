# TODO: Temporarily disabled due to importing old code into openshift-ansible
# repo. We will work on these over time.
# pylint: disable=bad-continuation,missing-docstring,no-self-use,invalid-name,no-value-for-parameter

import click
import os
import re
import sys
from ooinstall import openshift_ansible
from ooinstall import OOConfig
from ooinstall.oo_config import OOConfigInvalidHostError
from ooinstall.oo_config import Host
from ooinstall.variants import find_variant, get_variant_version_combos

DEFAULT_ANSIBLE_CONFIG = '/usr/share/atomic-openshift-utils/ansible.cfg'
DEFAULT_PLAYBOOK_DIR = '/usr/share/ansible/openshift-ansible/'

def validate_ansible_dir(path):
    if not path:
        raise click.BadParameter('An ansible path must be provided')
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
    if '' == hostname or is_valid_hostname(hostname):
        return hostname
    raise click.BadParameter('Invalid hostname. Please double-check this value and re-enter it.')

def get_ansible_ssh_user():
    click.clear()
    message = """
This installation process will involve connecting to remote hosts via ssh.  Any
account may be used however if a non-root account is used it must have
passwordless sudo access.
"""
    click.echo(message)
    return click.prompt('User for ssh access', default='root')

def get_master_routingconfig_subdomain():
    click.clear()
    message = """
You might want to override the default subdomain uses for exposed routes. If you don't know what
this is, use the default value.
"""
    click.echo(message)
    return click.prompt('New default subdomain (ENTER for none)', default='')

def list_hosts(hosts):
    hosts_idx = range(len(hosts))
    for idx in hosts_idx:
        click.echo('   {}: {}'.format(idx, hosts[idx]))

def delete_hosts(hosts):
    while True:
        list_hosts(hosts)
        del_idx = click.prompt('Select host to delete, y/Y to confirm, ' \
                               'or n/N to add more hosts', default='n')
        try:
            del_idx = int(del_idx)
            hosts.remove(hosts[del_idx])
        except IndexError:
            click.echo("\"{}\" doesn't match any hosts listed.".format(del_idx))
        except ValueError:
            try:
                response = del_idx.lower()
                if response in ['y', 'n']:
                    return hosts, response
                click.echo("\"{}\" doesn't coorespond to any valid input.".format(del_idx))
            except AttributeError:
                click.echo("\"{}\" doesn't coorespond to any valid input.".format(del_idx))
    return hosts, None

def collect_hosts(oo_cfg, existing_env=False, masters_set=False, print_summary=True):
    """
        Collect host information from user. This will later be filled in using
        ansible.

        Returns: a list of host information collected from the user
    """
    click.clear()
    click.echo('*** Host Configuration ***')
    message = """
You must now specify the hosts that will compose your OpenShift cluster.

Please enter an IP or hostname to connect to for each system in the cluster.
You will then be prompted to identify what role you would like this system to
serve in the cluster.

OpenShift Masters serve the API and web console and coordinate the jobs to run
across the environment.  If desired you can specify multiple Master systems for
an HA deployment, in which case you will be prompted to identify a *separate*
system to act as the load balancer for your cluster after all Masters and Nodes
are defined.

If only one Master is specified, an etcd instance embedded within the OpenShift
Master service will be used as the datastore.  This can be later replaced with a
separate etcd instance if desired.  If multiple Masters are specified, a
separate etcd cluster will be configured with each Master serving as a member.

Any Masters configured as part of this installation process will also be
configured as Nodes.  This is so that the Master will be able to proxy to Pods
from the API.  By default this Node will be unschedulable but this can be changed
after installation with 'oadm manage-node'.

OpenShift Nodes provide the runtime environments for containers.  They will
host the required services to be managed by the Master.

http://docs.openshift.com/enterprise/latest/architecture/infrastructure_components/kubernetes_infrastructure.html#master
http://docs.openshift.com/enterprise/latest/architecture/infrastructure_components/kubernetes_infrastructure.html#node
    """
    click.echo(message)

    hosts = []
    more_hosts = True
    num_masters = 0
    while more_hosts:
        host_props = {}
        host_props['connect_to'] = click.prompt('Enter hostname or IP address',
                                                value_proc=validate_prompt_hostname)

        if not masters_set:
            if click.confirm('Will this host be an OpenShift Master?'):
                host_props['master'] = True
                num_masters += 1

                if oo_cfg.settings['variant_version'] == '3.0':
                    masters_set = True
        host_props['node'] = True

        host_props['containerized'] = False
        if oo_cfg.settings['variant_version'] != '3.0':
            rpm_or_container = click.prompt('Will this host be RPM or Container based (rpm/container)?',
                                            type=click.Choice(['rpm', 'container']),
                                            default='rpm')
            if rpm_or_container == 'container':
                host_props['containerized'] = True

        if existing_env:
            host_props['new_host'] = True
        else:
            host_props['new_host'] = False

        host = Host(**host_props)

        hosts.append(host)

        if print_summary:
            print_installation_summary(hosts, oo_cfg.settings['variant_version'])

        # If we have one master, this is enough for an all-in-one deployment,
        # thus we can start asking if you wish to proceed. Otherwise we assume
        # you must.
        if masters_set or num_masters != 2:
            more_hosts = click.confirm('Do you want to add additional hosts?')

    if num_masters >= 3:
        collect_master_lb(hosts)

    return hosts


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

    masters = [host for host in hosts if host.master]
    nodes = [host for host in hosts if host.node]
    dedicated_nodes = [host for host in hosts if host.node and not host.master]
    click.echo('')
    click.echo('Total OpenShift Masters: %s' % len(masters))
    click.echo('Total OpenShift Nodes: %s' % len(nodes))

    if len(masters) == 1 and version != '3.0':
        ha_hint_message = """
NOTE: Add a total of 3 or more Masters to perform an HA installation."""
        click.echo(ha_hint_message)
    elif len(masters) == 2:
        min_masters_message = """
WARNING: A minimum of 3 masters are required to perform an HA installation.
Please add one more to proceed."""
        click.echo(min_masters_message)
    elif len(masters) >= 3:
        ha_message = """
NOTE: Multiple Masters specified, this will be an HA deployment with a separate
etcd cluster. You will be prompted to provide the FQDN of a load balancer once
finished entering hosts."""
        click.echo(ha_message)

        dedicated_nodes_message = """
WARNING: Dedicated Nodes are recommended for an HA deployment. If no dedicated
Nodes are specified, each configured Master will be marked as a schedulable
Node."""

        min_ha_nodes_message = """
WARNING: A minimum of 3 dedicated Nodes are recommended for an HA
deployment."""
        if len(dedicated_nodes) == 0:
            click.echo(dedicated_nodes_message)
        elif len(dedicated_nodes) < 3:
            click.echo(min_ha_nodes_message)

    click.echo('')


def print_host_summary(all_hosts, host):
    click.echo("- %s" % host.connect_to)
    if host.master:
        click.echo("  - OpenShift Master")
    if host.node:
        if host.is_dedicated_node():
            click.echo("  - OpenShift Node (Dedicated)")
        elif host.is_schedulable_node(all_hosts):
            click.echo("  - OpenShift Node")
        else:
            click.echo("  - OpenShift Node (Unscheduled)")
    if host.master_lb:
        if host.preconfigured:
            click.echo("  - Load Balancer (Preconfigured)")
        else:
            click.echo("  - Load Balancer (HAProxy)")
    if host.master:
        if host.is_etcd_member(all_hosts):
            click.echo("  - Etcd Member")
        else:
            click.echo("  - Etcd (Embedded)")


def collect_master_lb(hosts):
    """
    Get a valid load balancer from the user and append it to the list of
    hosts.

    Ensure user does not specify a system already used as a master/node as
    this is an invalid configuration.
    """
    message = """
Setting up High Availability Masters requires a load balancing solution.
Please provide a the FQDN of a host that will be configured as a proxy. This
can be either an existing load balancer configured to balance all masters on
port 8443 or a new host that will have HAProxy installed on it.

If the host provided does is not yet configured, a reference haproxy load
balancer will be installed.  It's important to note that while the rest of the
environment will be fault tolerant this reference load balancer will not be.
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
            if host.connect_to == hostname and (host.master or host.node):
                raise click.BadParameter('Cannot re-use "%s" as a load balancer, '
                                         'please specify a separate host' % hostname)
        return hostname

    host_props['connect_to'] = click.prompt('Enter hostname or IP address',
                                            value_proc=validate_prompt_lb)
    install_haproxy = click.confirm('Should the reference haproxy load balancer be installed on this host?')
    host_props['preconfigured'] = not install_haproxy
    host_props['master'] = False
    host_props['node'] = False
    host_props['master_lb'] = True
    master_lb = Host(**host_props)
    hosts.append(master_lb)

def confirm_hosts_facts(oo_cfg, callback_facts):
    hosts = oo_cfg.hosts
    click.clear()
    message = """
A list of the facts gathered from the provided hosts follows. Because it is
often the case that the hostname for a system inside the cluster is different
from the hostname that is resolveable from command line or web clients
these settings cannot be validated automatically.

For some cloud providers the installer is able to gather metadata exposed in
the instance so reasonable defaults will be provided.

Plese confirm that they are correct before moving forward.

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
 * The public hostname should resolve to the external ip from hosts outside of
   the cloud.
"""

    # For testing purposes we need to click.echo only once, so build up
    # the message:
    output = message

    default_facts_lines = []
    default_facts = {}
    for h in hosts:
        if h.preconfigured == True:
            continue
        default_facts[h.connect_to] = {}
        h.ip = callback_facts[h.connect_to]["common"]["ip"]
        h.public_ip = callback_facts[h.connect_to]["common"]["public_ip"]
        h.hostname = callback_facts[h.connect_to]["common"]["hostname"]
        h.public_hostname = callback_facts[h.connect_to]["common"]["public_hostname"]

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
    masters = [host for host in oo_cfg.hosts if host.master]

    if len(masters) == 2:
        click.echo("A minimum of 3 Masters are required for HA deployments.")
        sys.exit(1)

    if len(masters) > 1:
        master_lb = [host for host in oo_cfg.hosts if host.master_lb]
        if len(master_lb) > 1:
            click.echo('ERROR: More than one Master load balancer specified. Only one is allowed.')
            sys.exit(1)
        elif len(master_lb) == 1:
            if master_lb[0].master or master_lb[0].node:
                click.echo('ERROR: The Master load balancer is configured as a master or node. Please correct this.')
                sys.exit(1)
        else:
            message = """
ERROR: No master load balancer specified in config. You must provide the FQDN
of a load balancer to balance the API (port 8443) on all Master hosts.

https://docs.openshift.org/latest/install_config/install/advanced_install.html#multiple-masters
"""
            click.echo(message)
            sys.exit(1)

    dedicated_nodes = [host for host in oo_cfg.hosts if host.node and not host.master]
    if len(dedicated_nodes) == 0:
        message = """
WARNING: No dedicated Nodes specified. By default, colocated Masters have
their Nodes set to unschedulable.  If you proceed all nodes will be labelled
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
        message = "%s\n(%s) %s %s" % (message, i, variant.description,
            version.name)
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
    if not oo_cfg.hosts:
        missing_info = True
        click.echo('For unattended installs, hosts must be specified on the '
                   'command line or in the config file: %s' % oo_cfg.config_path)
        sys.exit(1)

    if 'ansible_ssh_user' not in oo_cfg.settings:
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

    missing_facts = oo_cfg.calc_missing_facts()
    if len(missing_facts) > 0:
        missing_info = True
        click.echo('For unattended installs, facts must be provided for all masters/nodes:')
        for host in missing_facts:
            click.echo('Host "%s" missing facts: %s' % (host, ", ".join(missing_facts[host])))

    if missing_info:
        sys.exit(1)


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
  the installer but also from within the cluster.

When the process completes you will have a default configuration for Masters
and Nodes.  For ongoing environment maintenance it's recommended that the
official Ansible playbooks be used.

For more information on installation prerequisites please see:
https://docs.openshift.com/enterprise/latest/admin_guide/install/prerequisites.html
"""
    confirm_continue(message)
    click.clear()

    if oo_cfg.settings.get('ansible_ssh_user', '') == '':
        oo_cfg.settings['ansible_ssh_user'] = get_ansible_ssh_user()
        click.clear()

    if oo_cfg.settings.get('variant', '') == '':
        variant, version = get_variant_and_version()
        oo_cfg.settings['variant'] = variant.name
        oo_cfg.settings['variant_version'] = version.name
        click.clear()

    if not oo_cfg.hosts:
        oo_cfg.hosts = collect_hosts(oo_cfg)
        click.clear()

    if not oo_cfg.settings.get('master_routingconfig_subdomain', None):
        oo_cfg.settings['master_routingconfig_subdomain'] = get_master_routingconfig_subdomain()
        click.clear()

    return oo_cfg


def collect_new_nodes(oo_cfg):
    click.clear()
    click.echo('*** New Node Configuration ***')
    message = """
Add new nodes here
    """
    click.echo(message)
    return collect_hosts(oo_cfg, existing_env=True, masters_set=True, print_summary=False)

def get_installed_hosts(hosts, callback_facts):
    installed_hosts = []
    for host in hosts:
        if(host.connect_to in callback_facts.keys()
           and 'common' in callback_facts[host.connect_to].keys()
           and callback_facts[host.connect_to]['common'].get('version', '')
           and callback_facts[host.connect_to]['common'].get('version', '') != 'None'):
            installed_hosts.append(host)
    return installed_hosts

# pylint: disable=too-many-branches
# This pylint error will be corrected shortly in separate PR.
def get_hosts_to_run_on(oo_cfg, callback_facts, unattended, force, verbose):

    # Copy the list of existing hosts so we can remove any already installed nodes.
    hosts_to_run_on = list(oo_cfg.hosts)

    # Check if master or nodes already have something installed
    installed_hosts = get_installed_hosts(oo_cfg.hosts, callback_facts)
    if len(installed_hosts) > 0:
        click.echo('Installed environment detected.')
        # This check has to happen before we start removing hosts later in this method
        if not force:
            if not unattended:
                click.echo('By default the installer only adds new nodes ' \
                           'to an installed environment.')
                response = click.prompt('Do you want to (1) only add additional nodes or ' \
                                        '(2) reinstall the existing hosts ' \
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
            if host.master:
                click.echo("{} is already an OpenShift Master".format(host))
                # Masters stay in the list, we need to run against them when adding
                # new nodes.
            elif host.node:
                click.echo("{} is already an OpenShift Node".format(host))
                # force is only used for reinstalls so we don't want to remove
                # anything.
                if not force:
                    hosts_to_run_on.remove(host)

        # Handle the cases where we know about uninstalled systems
        new_hosts = set(hosts_to_run_on) - set(installed_hosts)
        if len(new_hosts) > 0:
            for new_host in new_hosts:
                click.echo("{} is currently uninstalled".format(new_host))

            # Fall through
            click.echo('Adding additional nodes...')
        else:
            if unattended:
                if not force:
                    click.echo('Installed environment detected and no additional ' \
                               'nodes specified: aborting. If you want a fresh install, use ' \
                               '`atomic-openshift-installer install --force`')
                    sys.exit(1)
            else:
                if not force:
                    new_nodes = collect_new_nodes(oo_cfg)

                    hosts_to_run_on.extend(new_nodes)
                    oo_cfg.hosts.extend(new_nodes)

                    openshift_ansible.set_config(oo_cfg)
                    click.echo('Gathering information from hosts...')
                    callback_facts, error = openshift_ansible.default_facts(oo_cfg.hosts, verbose)
                    if error:
                        click.echo("There was a problem fetching the required information. See " \
                                   "{} for details.".format(oo_cfg.settings['ansible_log_path']))
                        sys.exit(1)
                else:
                    pass # proceeding as normal should do a clean install

    return hosts_to_run_on, callback_facts


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
@click.option('--ansible-config',
    type=click.Path(file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True),
    default=None)
@click.option('--ansible-log-path',
    type=click.Path(file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True),
    default="/tmp/ansible.log")
@click.option('-v', '--verbose',
    is_flag=True, default=False)
#pylint: disable=too-many-arguments
#pylint: disable=line-too-long
# Main CLI entrypoint, not much we can do about too many arguments.
def cli(ctx, unattended, configuration, ansible_playbook_directory, ansible_config, ansible_log_path, verbose):
    """
    atomic-openshift-installer makes the process for installing OSE or AEP
    easier by interactively gathering the data needed to run on each host.
    It can also be run in unattended mode if provided with a configuration file.

    Further reading: https://docs.openshift.com/enterprise/latest/install_config/install/quick_install.html
    """
    ctx.obj = {}
    ctx.obj['unattended'] = unattended
    ctx.obj['configuration'] = configuration
    ctx.obj['ansible_config'] = ansible_config
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

    if ctx.obj['ansible_config']:
        oo_cfg.settings['ansible_config'] = ctx.obj['ansible_config']
    elif 'ansible_config' not in oo_cfg.settings and \
        os.path.exists(DEFAULT_ANSIBLE_CONFIG):
        # If we're installed by RPM this file should exist and we can use it as our default:
        oo_cfg.settings['ansible_config'] = DEFAULT_ANSIBLE_CONFIG

    oo_cfg.settings['ansible_log_path'] = ctx.obj['ansible_log_path']

    ctx.obj['oo_cfg'] = oo_cfg
    openshift_ansible.set_config(oo_cfg)


@click.command()
@click.pass_context
def uninstall(ctx):
    oo_cfg = ctx.obj['oo_cfg']
    verbose = ctx.obj['verbose']

    if len(oo_cfg.hosts) == 0:
        click.echo("No hosts defined in: %s" % oo_cfg.config_path)
        sys.exit(1)

    click.echo("OpenShift will be uninstalled from the following hosts:\n")
    if not ctx.obj['unattended']:
        # Prompt interactively to confirm:
        for host in oo_cfg.hosts:
            click.echo("  * %s" % host.connect_to)
        proceed = click.confirm("\nDo you wish to proceed?")
        if not proceed:
            click.echo("Uninstall cancelled.")
            sys.exit(0)

    openshift_ansible.run_uninstall_playbook(verbose)


@click.command()
@click.pass_context
def upgrade(ctx):
    oo_cfg = ctx.obj['oo_cfg']
    verbose = ctx.obj['verbose']

    if len(oo_cfg.hosts) == 0:
        click.echo("No hosts defined in: %s" % oo_cfg.config_path)
        sys.exit(1)

    # Update config to reflect the version we're targetting, we'll write
    # to disk once ansible completes successfully, not before.
    old_variant = oo_cfg.settings['variant']
    old_version = oo_cfg.settings['variant_version']
    if oo_cfg.settings['variant'] == 'enterprise':
        oo_cfg.settings['variant'] = 'openshift-enterprise'
    version = find_variant(oo_cfg.settings['variant'])[1]
    oo_cfg.settings['variant_version'] = version.name
    click.echo("Openshift will be upgraded from %s %s to %s %s on the following hosts:\n" % (
        old_variant, old_version, oo_cfg.settings['variant'],
        oo_cfg.settings['variant_version']))
    for host in oo_cfg.hosts:
        click.echo("  * %s" % host.connect_to)

    if not ctx.obj['unattended']:
        # Prompt interactively to confirm:
        proceed = click.confirm("\nDo you wish to proceed?")
        if not proceed:
            click.echo("Upgrade cancelled.")
            sys.exit(0)

    retcode = openshift_ansible.run_upgrade_playbook(verbose)
    if retcode > 0:
        click.echo("Errors encountered during upgrade, please check %s." %
            oo_cfg.settings['ansible_log_path'])
    else:
        oo_cfg.save_to_disk()
        click.echo("Upgrade completed! Rebooting all hosts is recommended.")


@click.command()
@click.option('--force', '-f', is_flag=True, default=False)
@click.pass_context
def install(ctx, force):
    oo_cfg = ctx.obj['oo_cfg']
    verbose = ctx.obj['verbose']

    if ctx.obj['unattended']:
        error_if_missing_info(oo_cfg)
    else:
        oo_cfg = get_missing_info_from_user(oo_cfg)

    check_hosts_config(oo_cfg, ctx.obj['unattended'])

    print_installation_summary(oo_cfg.hosts, oo_cfg.settings.get('variant_version', None))
    click.echo('Gathering information from hosts...')
    callback_facts, error = openshift_ansible.default_facts(oo_cfg.hosts,
        verbose)
    if error:
        click.echo("There was a problem fetching the required information. " \
                   "Please see {} for details.".format(oo_cfg.settings['ansible_log_path']))
        sys.exit(1)

    hosts_to_run_on, callback_facts = get_hosts_to_run_on(
        oo_cfg, callback_facts, ctx.obj['unattended'], force, verbose)

    click.echo('Writing config to: %s' % oo_cfg.config_path)

    # We already verified this is not the case for unattended installs, so this can
    # only trigger for live CLI users:
    # TODO: if there are *new* nodes and this is a live install, we may need the  user
    # to confirm the settings for new nodes. Look into this once we're distinguishing
    # between new and pre-existing nodes.
    if len(oo_cfg.calc_missing_facts()) > 0:
        confirm_hosts_facts(oo_cfg, callback_facts)

    oo_cfg.save_to_disk()

    click.echo('Ready to run installation process.')
    message = """
If changes are needed please edit the config file above and re-run.
"""
    if not ctx.obj['unattended']:
        confirm_continue(message)

    error = openshift_ansible.run_main_playbook(oo_cfg.hosts,
                                                   hosts_to_run_on, verbose)
    if error:
        # The bootstrap script will print out the log location.
        message = """
An error was detected.  After resolving the problem please relaunch the
installation process.
"""
        click.echo(message)
        sys.exit(1)
    else:
        message = """
The installation was successful!

If this is your first time installing please take a look at the Administrator
Guide for advanced options related to routing, storage, authentication and much
more:

http://docs.openshift.com/enterprise/latest/admin_guide/overview.html
"""
        click.echo(message)
        click.pause()

cli.add_command(install)
cli.add_command(upgrade)
cli.add_command(uninstall)

if __name__ == '__main__':
    # This is expected behaviour for context passing with click library:
    # pylint: disable=unexpected-keyword-arg
    cli(obj={})
