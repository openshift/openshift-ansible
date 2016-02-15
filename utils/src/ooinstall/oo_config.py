# TODO: Temporarily disabled due to importing old code into openshift-ansible
# repo. We will work on these over time.
# pylint: disable=bad-continuation,missing-docstring,no-self-use,invalid-name,too-many-instance-attributes,too-few-public-methods

import os
import yaml
from pkg_resources import resource_filename

PERSIST_SETTINGS = [
    'ansible_ssh_user',
    'ansible_config',
    'ansible_log_path',
    'master_routingconfig_subdomain',
    'variant',
    'variant_version',
    'version',
    ]
DEFAULT_REQUIRED_FACTS = ['ip', 'public_ip', 'hostname', 'public_hostname']
PRECONFIGURED_REQUIRED_FACTS = ['hostname', 'public_hostname']


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
        self.new_host = kwargs.get('new_host', None)

        # Should this host run as an OpenShift master:
        self.master = kwargs.get('master', False)

        # Should this host run as an OpenShift node:
        self.node = kwargs.get('node', False)

        # Should this host run as an HAProxy:
        self.master_lb = kwargs.get('master_lb', False)

        self.containerized = kwargs.get('containerized', False)

        if self.connect_to is None:
            raise OOConfigInvalidHostError("You must specify either an ip " \
                "or hostname as 'connect_to'")

        if self.master is False and self.node is False and self.master_lb is False:
            raise OOConfigInvalidHostError(
                "You must specify each host as either a master or a node.")

    def __str__(self):
        return self.connect_to

    def __repr__(self):
        return self.connect_to

    def to_dict(self):
        """ Used when exporting to yaml. """
        d = {}
        for prop in ['ip', 'hostname', 'public_ip', 'public_hostname',
                     'master', 'node', 'master_lb', 'containerized',
                     'connect_to', 'preconfigured', 'new_host']:
            # If the property is defined (not None or False), export it:
            if getattr(self, prop):
                d[prop] = getattr(self, prop)
        return d

    def is_etcd_member(self, all_hosts):
        """ Will this host be a member of a standalone etcd cluster. """
        if not self.master:
            return False
        masters = [host for host in all_hosts if host.master]
        if len(masters) > 1:
            return True
        return False

    def is_dedicated_node(self):
        """ Will this host be a dedicated node. (not a master) """
        return self.node and not self.master

    def is_schedulable_node(self, all_hosts):
        """ Will this host be a node marked as schedulable. """
        if not self.node:
            return False
        if not self.master:
            return True

        masters = [host for host in all_hosts if host.master]
        nodes = [host for host in all_hosts if host.node]
        if len(masters) == len(nodes):
            return True
        return False


class OOConfig(object):
    default_dir = os.path.normpath(
        os.environ.get('XDG_CONFIG_HOME',
                       os.environ['HOME'] + '/.config/') + '/openshift/')
    default_file = '/installer.cfg.yml'

    def __init__(self, config_path):
        if config_path:
            self.config_path = os.path.normpath(config_path)
        else:
            self.config_path = os.path.normpath(self.default_dir +
                                                self.default_file)
        self.settings = {}
        self._read_config()
        self._set_defaults()

    def _read_config(self):
        self.hosts = []
        try:
            if os.path.exists(self.config_path):
                cfgfile = open(self.config_path, 'r')
                self.settings = yaml.safe_load(cfgfile.read())
                cfgfile.close()

                # Use the presence of a Description as an indicator this is
                # a legacy config file:
                if 'Description' in self.settings:
                    self._upgrade_legacy_config()

                # Parse the hosts into DTO objects:
                if 'hosts' in self.settings:
                    for host in self.settings['hosts']:
                        self.hosts.append(Host(**host))

                # Watchout for the variant_version coming in as a float:
                if 'variant_version' in self.settings:
                    self.settings['variant_version'] = \
                        str(self.settings['variant_version'])

        except IOError, ferr:
            raise OOConfigFileError('Cannot open config file "{}": {}'.format(ferr.filename,
                                                                              ferr.strerror))
        except yaml.scanner.ScannerError:
            raise OOConfigFileError('Config file "{}" is not a valid YAML document'.format(self.config_path))

    def _upgrade_legacy_config(self):
        new_hosts = []
        remove_settings = ['validated_facts', 'Description', 'Name',
            'Subscription', 'Vendor', 'Version', 'masters', 'nodes']

        if 'validated_facts' in self.settings:
            for key, value in self.settings['validated_facts'].iteritems():
                value['connect_to'] = key
                if 'masters' in self.settings and key in self.settings['masters']:
                    value['master'] = True
                if 'nodes' in self.settings and key in self.settings['nodes']:
                    value['node'] = True
                new_hosts.append(value)
        self.settings['hosts'] = new_hosts

        for s in remove_settings:
            if s in self.settings:
                del self.settings[s]

        # A legacy config implies openshift-enterprise 3.0:
        self.settings['variant'] = 'openshift-enterprise'
        self.settings['variant_version'] = '3.0'

    def _set_defaults(self):

        if 'ansible_inventory_directory' not in self.settings:
            self.settings['ansible_inventory_directory'] = \
                self._default_ansible_inv_dir()
        if not os.path.exists(self.settings['ansible_inventory_directory']):
            os.makedirs(self.settings['ansible_inventory_directory'])
        if 'ansible_plugins_directory' not in self.settings:
            self.settings['ansible_plugins_directory'] = resource_filename(__name__, 'ansible_plugins')
        if 'version' not in self.settings:
            self.settings['version'] = 'v1'

        if 'ansible_callback_facts_yaml' not in self.settings:
            self.settings['ansible_callback_facts_yaml'] = '%s/callback_facts.yaml' % \
                self.settings['ansible_inventory_directory']

        if 'ansible_ssh_user' not in self.settings:
            self.settings['ansible_ssh_user'] = ''

        self.settings['ansible_inventory_path'] = '{}/hosts'.format(self.settings['ansible_inventory_directory'])

        # clean up any empty sets
        for setting in self.settings.keys():
            if not self.settings[setting]:
                self.settings.pop(setting)

    def _default_ansible_inv_dir(self):
        return os.path.normpath(
            os.path.dirname(self.config_path) + "/.ansible")

    def calc_missing_facts(self):
        """
        Determine which host facts are not defined in the config.

        Returns a hash of host to a list of the missing facts.
        """
        result = {}

        for host in self.hosts:
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
        for setting in PERSIST_SETTINGS:
            if setting in self.settings and self.settings[setting]:
                p_settings[setting] = self.settings[setting]
        p_settings['hosts'] = []
        for host in self.hosts:
            p_settings['hosts'].append(host.to_dict())

        if self.settings['ansible_inventory_directory'] != \
                self._default_ansible_inv_dir():
            p_settings['ansible_inventory_directory'] = \
                self.settings['ansible_inventory_directory']

        return p_settings

    def yaml(self):
        return yaml.safe_dump(self.persist_settings(), default_flow_style=False)

    def __str__(self):
        return self.yaml()

    def get_host(self, name):
        for host in self.hosts:
            if host.connect_to == name:
                return host
        return None
