# pylint: disable=bad-continuation,missing-docstring,no-self-use,invalid-name,too-many-instance-attributes,too-few-public-methods

from __future__ import (absolute_import, print_function)

import os
import sys
import logging
import yaml
from pkg_resources import resource_filename


installer_log = logging.getLogger('installer')

CONFIG_PERSIST_SETTINGS = [
    'ansible_ssh_user',
    'ansible_callback_facts_yaml',
    'ansible_inventory_path',
    'ansible_log_path',
    'deployment',
    'version',
    'variant',
    'variant_subtype',
    'variant_version',
]

DEPLOYMENT_VARIABLES_BLACKLIST = [
    'hosts',
    'roles',
]

HOST_VARIABLES_BLACKLIST = [
    'ip',
    'public_ip',
    'hostname',
    'public_hostname',
    'node_labels',
    'containerized',
    'preconfigured',
    'schedulable',
    'other_variables',
    'roles',
]

DEFAULT_REQUIRED_FACTS = ['ip', 'public_ip', 'hostname', 'public_hostname']
PRECONFIGURED_REQUIRED_FACTS = ['hostname', 'public_hostname']


def print_read_config_error(error, path='the configuration file'):
    message = """
Error loading config. {}.

See https://docs.openshift.com/enterprise/latest/install_config/install/quick_install.html#defining-an-installation-configuration-file
for information on creating a configuration file or delete {} and re-run the installer.
"""
    print(message.format(error, path))


class OOConfigFileError(Exception):
    """The provided config file path can't be read/written
    """
    pass


class OOConfigInvalidHostError(Exception):
    """ Host in config is missing both ip and hostname. """
    pass


class Host(object):
    """ A system we will or have installed OpenShift on. """
    def __init__(self, **kwargs):
        self.ip = kwargs.get('ip', None)
        self.hostname = kwargs.get('hostname', None)
        self.public_ip = kwargs.get('public_ip', None)
        self.public_hostname = kwargs.get('public_hostname', None)
        self.connect_to = kwargs.get('connect_to', None)

        self.preconfigured = kwargs.get('preconfigured', None)
        self.schedulable = kwargs.get('schedulable', None)
        self.new_host = kwargs.get('new_host', None)
        self.containerized = kwargs.get('containerized', False)
        self.node_labels = kwargs.get('node_labels', '')

        # allowable roles: master, node, etcd, storage, master_lb
        self.roles = kwargs.get('roles', [])

        self.other_variables = kwargs.get('other_variables', {})

        if self.connect_to is None:
            raise OOConfigInvalidHostError(
                "You must specify either an ip or hostname as 'connect_to'")

    def __str__(self):
        return self.connect_to

    def __repr__(self):
        return self.connect_to

    def to_dict(self):
        """ Used when exporting to yaml. """
        d = {}

        for prop in ['ip', 'hostname', 'public_ip', 'public_hostname', 'connect_to',
                     'preconfigured', 'containerized', 'schedulable', 'roles', 'node_labels', ]:
            # If the property is defined (not None or False), export it:
            if getattr(self, prop):
                d[prop] = getattr(self, prop)
        for variable, value in self.other_variables.items():
            d[variable] = value

        return d

    def is_master(self):
        return 'master' in self.roles

    def is_node(self):
        return 'node' in self.roles

    def is_master_lb(self):
        return 'master_lb' in self.roles

    def is_storage(self):
        return 'storage' in self.roles

    def is_etcd(self):
        """ Does this host have the etcd role """
        return 'etcd' in self.roles

    def is_dedicated_node(self):
        """ Will this host be a dedicated node. (not a master) """
        return self.is_node() and not self.is_master()

    def is_schedulable_node(self, all_hosts):
        """ Will this host be a node marked as schedulable. """
        if not self.is_node():
            return False
        if not self.is_master():
            return True

        masters = [host for host in all_hosts if host.is_master()]
        nodes = [host for host in all_hosts if host.is_node()]
        if len(masters) == len(nodes):
            return True
        return False


class Role(object):
    """ A role that will be applied to a host. """
    def __init__(self, name, variables):
        self.name = name
        self.variables = variables

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def to_dict(self):
        """ Used when exporting to yaml. """
        d = {}
        for prop in ['name', 'variables']:
            # If the property is defined (not None or False), export it:
            if getattr(self, prop):
                d[prop] = getattr(self, prop)
        return d


class Deployment(object):
    def __init__(self, **kwargs):
        self.hosts = kwargs.get('hosts', [])
        self.roles = kwargs.get('roles', {})
        self.variables = kwargs.get('variables', {})


class OOConfig(object):
    default_dir = os.path.normpath(
        os.environ.get('XDG_CONFIG_HOME',
                       os.environ.get('HOME', '') + '/.config/') + '/openshift/')
    default_file = '/installer.cfg.yml'

    def __init__(self, config_path):
        if config_path:
            self.config_path = os.path.normpath(config_path)
        else:
            self.config_path = os.path.normpath(self.default_dir +
                                                self.default_file)
        self.deployment = Deployment(hosts=[], roles={}, variables={})
        self.settings = {}
        self._read_config()
        self._set_defaults()

    # pylint: disable=too-many-branches
    #         Lots of different checks ran in a single method, could
    #         use a little refactoring-love some time
    def _read_config(self):
        installer_log.debug("Attempting to read the OO Config")
        try:
            installer_log.debug("Attempting to see if the provided config file exists: %s", self.config_path)
            if os.path.exists(self.config_path):
                installer_log.debug("We think the config file exists: %s", self.config_path)
                with open(self.config_path, 'r') as cfgfile:
                    loaded_config = yaml.safe_load(cfgfile.read())

                if 'version' not in loaded_config:
                    print_read_config_error('Legacy configuration file found', self.config_path)
                    sys.exit(0)

                if loaded_config.get('version', '') == 'v1':
                    loaded_config = self._upgrade_v1_config(loaded_config)

                try:
                    host_list = loaded_config['deployment']['hosts']
                    role_list = loaded_config['deployment']['roles']
                except KeyError as e:
                    print_read_config_error("No such key: {}".format(e), self.config_path)
                    sys.exit(0)

                for setting in CONFIG_PERSIST_SETTINGS:
                    persisted_value = loaded_config.get(setting)
                    if persisted_value is not None:
                        self.settings[setting] = str(persisted_value)
                        installer_log.debug("config: set (%s) to value (%s)", setting, persisted_value)

                # We've loaded any persisted configs, let's verify any
                # paths which are required for a correct and complete
                # install

                # - ansible_callback_facts_yaml - Settings from a
                #   pervious run. If the file doesn't exist then we
                #   will just warn about it for now and recollect the
                #   facts.
                if self.settings.get('ansible_callback_facts_yaml', None) is not None:
                    if not os.path.exists(self.settings['ansible_callback_facts_yaml']):
                        # Cached callback facts file does not exist
                        installer_log.warning("The specified 'ansible_callback_facts_yaml'"
                                              "file does not exist (%s)",
                                              self.settings['ansible_callback_facts_yaml'])
                        installer_log.debug("Remote system facts will be collected again later")
                        self.settings.pop('ansible_callback_facts_yaml')

                for setting in loaded_config['deployment']:
                    try:
                        if setting not in DEPLOYMENT_VARIABLES_BLACKLIST:
                            self.deployment.variables[setting] = \
                                str(loaded_config['deployment'][setting])
                    except KeyError:
                        continue

                # Parse the hosts into DTO objects:
                for host in host_list:
                    host['other_variables'] = {}
                    for variable, value in host.items():
                        if variable not in HOST_VARIABLES_BLACKLIST:
                            host['other_variables'][variable] = value
                    self.deployment.hosts.append(Host(**host))

                # Parse the roles into Objects
                for name, variables in role_list.items():
                    self.deployment.roles.update({name: Role(name, variables)})

        except IOError as ferr:
            raise OOConfigFileError('Cannot open config file "{}": {}'.format(ferr.filename,
                                                                              ferr.strerror))
        except yaml.scanner.ScannerError:
            raise OOConfigFileError(
                'Config file "{}" is not a valid YAML document'.format(self.config_path))
        installer_log.debug("Parsed the config file")

    def _upgrade_v1_config(self, config):
        new_config_data = {}
        new_config_data['deployment'] = {}
        new_config_data['deployment']['hosts'] = []
        new_config_data['deployment']['roles'] = {}
        new_config_data['deployment']['variables'] = {}

        role_list = {}

        if config.get('ansible_ssh_user', False):
            new_config_data['deployment']['ansible_ssh_user'] = config['ansible_ssh_user']

        if config.get('variant', False):
            new_config_data['variant'] = config['variant']

        if config.get('variant_version', False):
            new_config_data['variant_version'] = config['variant_version']

        for host in config['hosts']:
            host_props = {}
            host_props['roles'] = []
            host_props['connect_to'] = host['connect_to']

            for prop in ['ip', 'public_ip', 'hostname', 'public_hostname', 'containerized', 'preconfigured']:
                host_props[prop] = host.get(prop, None)

            for role in ['master', 'node', 'master_lb', 'storage', 'etcd']:
                if host.get(role, False):
                    host_props['roles'].append(role)
                    role_list[role] = ''

            new_config_data['deployment']['hosts'].append(host_props)

        new_config_data['deployment']['roles'] = role_list

        return new_config_data

    def _set_defaults(self):
        installer_log.debug("Setting defaults, current OOConfig settings: %s", self.settings)

        if 'ansible_inventory_directory' not in self.settings:
            self.settings['ansible_inventory_directory'] = self._default_ansible_inv_dir()

        if not os.path.exists(self.settings['ansible_inventory_directory']):
            installer_log.debug("'ansible_inventory_directory' does not exist, "
                                "creating it now (%s)",
                                self.settings['ansible_inventory_directory'])
            os.makedirs(self.settings['ansible_inventory_directory'])
        else:
            installer_log.debug("We think this 'ansible_inventory_directory' "
                                "is OK: %s",
                                self.settings['ansible_inventory_directory'])

        if 'ansible_plugins_directory' not in self.settings:
            self.settings['ansible_plugins_directory'] = \
                resource_filename(__name__, 'ansible_plugins')
            installer_log.debug("We think the ansible plugins directory should be: %s (it is not already set)",
                                self.settings['ansible_plugins_directory'])
        else:
            installer_log.debug("The ansible plugins directory is already set: %s",
                                self.settings['ansible_plugins_directory'])

        if 'version' not in self.settings:
            self.settings['version'] = 'v2'

        if 'ansible_callback_facts_yaml' not in self.settings:
            installer_log.debug("No 'ansible_callback_facts_yaml' in self.settings")
            self.settings['ansible_callback_facts_yaml'] = '%s/callback_facts.yaml' % \
                self.settings['ansible_inventory_directory']
            installer_log.debug("Value: %s", self.settings['ansible_callback_facts_yaml'])
        else:
            installer_log.debug("'ansible_callback_facts_yaml' already set "
                                "in self.settings: %s",
                                self.settings['ansible_callback_facts_yaml'])

        if 'ansible_ssh_user' not in self.settings:
            self.settings['ansible_ssh_user'] = ''

        if 'ansible_inventory_path' not in self.settings:
            self.settings['ansible_inventory_path'] = \
                '{}/hosts'.format(os.path.dirname(self.config_path))

        # clean up any empty sets
        empty_keys = []
        for setting in self.settings:
            if not self.settings[setting]:
                empty_keys.append(setting)
        for key in empty_keys:
            self.settings.pop(key)

        installer_log.debug("Updated OOConfig settings: %s", self.settings)

    def _default_ansible_inv_dir(self):
        return os.path.normpath(
            os.path.dirname(self.config_path) + "/.ansible")

    def calc_missing_facts(self):
        """
        Determine which host facts are not defined in the config.

        Returns a hash of host to a list of the missing facts.
        """
        result = {}

        for host in self.deployment.hosts:
            missing_facts = []
            if host.preconfigured:
                required_facts = PRECONFIGURED_REQUIRED_FACTS
            else:
                required_facts = DEFAULT_REQUIRED_FACTS

            for required_fact in required_facts:
                if not getattr(host, required_fact):
                    missing_facts.append(required_fact)
            if len(missing_facts) > 0:
                result[host.connect_to] = missing_facts
        return result

    def save_to_disk(self):
        out_file = open(self.config_path, 'w')
        out_file.write(self.yaml())
        out_file.close()

    def persist_settings(self):
        p_settings = {}

        for setting in CONFIG_PERSIST_SETTINGS:
            if setting in self.settings and self.settings[setting]:
                p_settings[setting] = self.settings[setting]

        p_settings['deployment'] = {}
        p_settings['deployment']['hosts'] = []
        p_settings['deployment']['roles'] = {}

        for host in self.deployment.hosts:
            p_settings['deployment']['hosts'].append(host.to_dict())

        for name, role in self.deployment.roles.items():
            p_settings['deployment']['roles'][name] = role.variables

        for setting in self.deployment.variables:
            if setting not in DEPLOYMENT_VARIABLES_BLACKLIST:
                p_settings['deployment'][setting] = self.deployment.variables[setting]

        try:
            p_settings['variant'] = self.settings['variant']
            p_settings['variant_version'] = self.settings['variant_version']

            if self.settings['ansible_inventory_directory'] != self._default_ansible_inv_dir():
                p_settings['ansible_inventory_directory'] = self.settings['ansible_inventory_directory']
        except KeyError as e:
            print("Error persisting settings: {}".format(e))
            sys.exit(0)

        return p_settings

    def yaml(self):
        return yaml.safe_dump(self.persist_settings(), default_flow_style=False)

    def __str__(self):
        return self.yaml()

    def get_host_roles_set(self):
        roles_set = set()
        for host in self.deployment.hosts:
            for role in host.roles:
                roles_set.add(role)

        return roles_set
