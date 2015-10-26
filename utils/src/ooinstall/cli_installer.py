import click
import os
import re
import sys
from ooinstall import install_transactions
from ooinstall import OOConfig
from ooinstall.oo_config import Host
from variants import find_variant, get_variant_version_combos

DEFAULT_ANSIBLE_CONFIG = '/usr/share/atomic-openshift-util/ansible.cfg'

def validate_ansible_dir(ctx, param, path):
    if not path:
        raise click.BadParameter('An ansible path must be provided')
    return path
    # if not os.path.exists(path)):
    #     raise click.BadParameter("Path \"{}\" doesn't exist".format(path))

def is_valid_hostname(hostname):
    if not hostname or len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1] # strip exactly one dot from the right, if present
    allowed = re.compile("(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))

def validate_hostname(ctx, param, hosts):
    # if '' == hostname or is_valid_hostname(hostname):
    for hostname in hosts:
        if not is_valid_hostname(hostname):
            raise click.BadParameter('"{}" appears to be an invalid hostname. ' \
                                     'Please double-check this value ' \
                                     'and re-enter it.'.format(hostname))
    return hosts

def validate_prompt_hostname(hostname):
    if '' == hostname or is_valid_hostname(hostname):
        return hostname
    raise click.BadParameter('"{}" appears to be an invalid hostname. ' \
                             'Please double-check this value i' \
                             'and re-enter it.'.format(hostname))

def get_ansible_ssh_user():
    click.clear()
    message = """
This installation process will involve connecting to remote hosts via ssh.  Any
account may be used however if a non-root account is used it must have
passwordless sudo access.
"""
    click.echo(message)
    return click.prompt('User for ssh access', default='root')

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

def collect_hosts():
    """
        Collect host information from user. This will later be filled in using
        ansible.

        Returns: a list of host information collected from the user
    """
    click.clear()
    click.echo('***Host Configuration***')
    message = """
The OpenShift Master serves the API and web console.  It also coordinates the
jobs that have to run across the environment.  It can even run the datastore.
For wizard based installations the database will be embedded.  It's possible to
change this later using etcd from Red Hat Enterprise Linux 7.

Any Masters configured as part of this installation process will also be
configured as Nodes.  This is so that the Master will be able to proxy to Pods
from the API.  By default this Node will be unscheduleable but this can be changed
after installation with 'oadm manage-node'.

The OpenShift Node provides the runtime environments for containers.  It will
host the required services to be managed by the Master.

http://docs.openshift.com/enterprise/latest/architecture/infrastructure_components/kubernetes_infrastructure.html#master
http://docs.openshift.com/enterprise/3.0/architecture/infrastructure_components/kubernetes_infrastructure.html#node
    """
    click.echo(message)

    hosts = []
    more_hosts = True
    ip_regex = re.compile(r'^\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}$')

    while more_hosts:
        host_props = {}
        hostname_or_ip = click.prompt('Enter hostname or IP address:',
                                      default='',
                                      value_proc=validate_prompt_hostname)

        if ip_regex.match(hostname_or_ip):
            host_props['ip'] = hostname_or_ip
        else:
            host_props['hostname'] = hostname_or_ip

        host_props['master'] = click.confirm('Will this host be an OpenShift Master?')
        host_props['node'] = True

        rpm_or_container = click.prompt('Will this host be RPM or Container based (rpm/container)?',
                                        type=click.Choice(['rpm', 'container']),
                                        default='rpm')
        if rpm_or_container == 'container':
            host_props['containerized'] = True
        else:
            host_props['containerized'] = False

        host = Host(**host_props)

        hosts.append(host)

        more_hosts = click.confirm('Do you want to add additional hosts?')
    return hosts

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

IP,public IP,hostname,public hostname

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
    validated_facts = {}
    for h in hosts:
        default_facts[h] = {}
        h.ip = callback_facts[str(h)]["common"]["ip"]
        h.public_ip = callback_facts[str(h)]["common"]["public_ip"]
        h.hostname = callback_facts[str(h)]["common"]["hostname"]
        h.public_hostname = callback_facts[str(h)]["common"]["public_hostname"]

        validated_facts[h] = {}
        default_facts_lines.append(",".join([h.ip,
                                             h.public_ip,
                                             h.hostname,
                                             h.public_hostname]))
        output = "%s\n%s" % (output, ",".join([h.ip,
                             h.public_ip,
                             h.hostname,
                             h.public_hostname]))

    output = "%s\n%s" % (output, notes)
    click.echo(output)
    facts_confirmed = click.confirm("Do the above facts look correct?")
    if not facts_confirmed:
        message = """
Edit %s with the desired values and rerun oo-install with --unattended .
""" % oo_cfg.config_path
        click.echo(message)
        # Make sure we actually write out the config file.
        oo_cfg.save_to_disk()
        sys.exit(0)
    return default_facts

def get_variant_and_version():
    message = "\nWhich variant would you like to install?\n\n"

    i = 1
    combos = get_variant_version_combos()
    for (variant, version) in combos:
        message = "%s\n(%s) %s %s" % (message, i, variant.description,
            version.name)
        i = i + 1

    click.echo(message)
    response = click.prompt("Choose a variant from above: ", default=1)
    product, version = combos[response - 1]

    return product, version

def confirm_continue(message):
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

    if not oo_cfg.hosts:
        oo_cfg.hosts = collect_hosts()
        click.clear()

    if oo_cfg.settings.get('variant', '') == '':
        variant, version = get_variant_and_version()
        oo_cfg.settings['variant'] = variant.name
        oo_cfg.settings['variant_version'] = version.name
        click.clear()

    return oo_cfg


def collect_new_nodes():
    click.clear()
    click.echo('***New Node Configuration***')
    message = """
Add new nodes here
    """
    click.echo(message)
    return collect_hosts()

def get_installed_hosts(hosts, callback_facts):
    installed_hosts = []
    for host in hosts:
        if(host.name in callback_facts.keys()
           and 'common' in callback_facts[host.name].keys()
           and callback_facts[host.name]['common'].get('version', '')
           and callback_facts[host.name]['common'].get('version', '') != 'None'):
            installed_hosts.append(host)
    return installed_hosts

def get_hosts_to_run_on(oo_cfg, callback_facts, unattended, force):

    # Copy the list of existing hosts so we can remove any already installed nodes.
    hosts_to_run_on = list(oo_cfg.hosts)

    # Check if master or nodes already have something installed
    installed_hosts = get_installed_hosts(oo_cfg.hosts, callback_facts)
    if len(installed_hosts) > 0:
        # present a message listing already installed hosts
        for host in installed_hosts:
            if host.master:
                click.echo("{} is already an OpenShift Master".format(host))
                # Masters stay in the list, we need to run against them when adding
                # new nodes.
            elif host.node:
                click.echo("{} is already an OpenShift Node".format(host))
                hosts_to_run_on.remove(host)
        # for unattended either continue if they force install or exit if they didn't
        if unattended:
            if not force:
                click.echo('Installed environment detected and no additional nodes specified: ' \
                           'aborting. If you want a fresh install, use --force')
                sys.exit(1)
        # for attended ask the user what to do
        else:
            click.echo('Installed environment detected and no additional nodes specified. ')
            response = click.prompt('Do you want to (1) add more nodes or ' \
                                    '(2) perform a clean install?', type=int)
            if response == 1: # add more nodes
                new_nodes = collect_new_nodes()

                hosts_to_run_on.extend(new_nodes)
                oo_cfg.hosts.extend(new_nodes)

                install_transactions.set_config(oo_cfg)
                callback_facts, error = install_transactions.default_facts(oo_cfg.hosts)
                if error:
                    click.echo("There was a problem fetching the required information. " \
                               "See {} for details.".format(oo_cfg.settings['ansible_log_path']))
                    sys.exit(1)
            else:
                pass # proceeding as normal should do a clean install

    return hosts_to_run_on, callback_facts

@click.command()
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
                              writable=True,
                              readable=True),
              # callback=validate_ansible_dir,
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
@click.option('--unattended', '-u', is_flag=True, default=False)
@click.option('--force', '-f', is_flag=True, default=False)
def main(configuration, ansible_playbook_directory, ansible_config, ansible_log_path, unattended, force):
    oo_cfg = OOConfig(configuration)

    if not ansible_playbook_directory:
        ansible_playbook_directory = oo_cfg.settings.get('ansible_playbook_directory', '')

    if ansible_config:
        oo_cfg.settings['ansible_config'] = ansible_config
    elif os.path.exists(DEFAULT_ANSIBLE_CONFIG):
        # If we're installed by RPM this file should exist and we can use it as our default:
        oo_cfg.settings['ansible_config'] = DEFAULT_ANSIBLE_CONFIG

    validate_ansible_dir(None, None, ansible_playbook_directory)
    oo_cfg.settings['ansible_playbook_directory'] = ansible_playbook_directory
    oo_cfg.ansible_playbook_directory = ansible_playbook_directory

    oo_cfg.settings['ansible_log_path'] = ansible_log_path
    install_transactions.set_config(oo_cfg)

    if unattended:
        error_if_missing_info(oo_cfg)
    else:
        oo_cfg = get_missing_info_from_user(oo_cfg)

    click.echo('Gathering information from hosts...')
    callback_facts, error = install_transactions.default_facts(oo_cfg.hosts)
    if error:
        click.echo("There was a problem fetching the required information. " \
                   "Please see {} for details.".format(oo_cfg.settings['ansible_log_path']))
        sys.exit(1)

    hosts_to_run_on, callback_facts = get_hosts_to_run_on(oo_cfg, callback_facts, unattended, force)


    click.echo('Writing config to: %s' % oo_cfg.config_path)

    # We already verified this is not the case for unattended installs, so this can
    # only trigger for live CLI users:
    # TODO: if there are *new* nodes and this is a live install, we may need the  user
    # to confirm the settings for new nodes. Look into this once we're distinguishing
    # between new and pre-existing nodes.
    if len(oo_cfg.calc_missing_facts()) > 0:
        validated_hosts = confirm_hosts_facts(oo_cfg, callback_facts)

    oo_cfg.save_to_disk()

    click.echo('Ready to run installation process.')
    message = """
If changes are needed to the values recorded by the installer please update {}.
""".format(oo_cfg.config_path)
    if not unattended:
        confirm_continue(message)

    error = install_transactions.run_main_playbook(oo_cfg.hosts,
                                                   hosts_to_run_on)
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

if __name__ == '__main__':
    main()
