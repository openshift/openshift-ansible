import os
import yaml
from pkg_resources import resource_filename

PERSIST_SETTINGS = [
    'ansible_ssh_user',
    'ansible_config',
    'ansible_log_path',
    'variant',
    'variant_version',
    ]
REQUIRED_FACTS = ['ip', 'public_ip', 'hostname', 'public_hostname']


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

        # Should this host run as an OpenShift master:
        self.master = kwargs.get('master', False)

        # Should this host run as an OpenShift node:
        self.node = kwargs.get('node', False)
        self.containerized = kwargs.get('containerized', False)

        if self.ip is None and self.hostname is None:
            raise OOConfigInvalidHostError("You must specify either 'ip' or 'hostname'")

        if self.master is False and self.node is False:
            raise OOConfigInvalidHostError(
                "You must specify each host as either a master or a node.")

        # Hosts can be specified with an ip, hostname, or both. However we need
        # something authoritative we can connect to and refer to the host by.
        # Preference given to the IP if specified as this is more specific.
        # We know one must be set by this point.
        self.name = self.ip if self.ip is not None else self.hostname

    def __str__(self):
        return self.name

    def __repr__(self):
        return self.name

    def to_dict(self):
        """ Used when exporting to yaml. """
        d = {}
        for prop in ['ip', 'hostname', 'public_ip', 'public_hostname',
                     'master', 'node', 'containerized']:
            # If the property is defined (not None or False), export it:
            if getattr(self, prop):
                d[prop] = getattr(self, prop)
        return d


class OOConfig(object):
    new_config = True
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
        self.read_config()
        self.set_defaults()

    def read_config(self, is_new=False):
        self.hosts = []
        try:
            new_settings = None
            if os.path.exists(self.config_path):
                cfgfile = open(self.config_path, 'r')
                new_settings = yaml.safe_load(cfgfile.read())
                cfgfile.close()
            if new_settings:
                self.settings = new_settings
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
        self.new_config = is_new

    def set_defaults(self):

        if 'ansible_inventory_directory' not in self.settings:
            self.settings['ansible_inventory_directory'] = \
                self._default_ansible_inv_dir()
        if not os.path.exists(self.settings['ansible_inventory_directory']):
            os.makedirs(self.settings['ansible_inventory_directory'])
        if 'ansible_plugins_directory' not in self.settings:
            self.settings['ansible_plugins_directory'] = resource_filename(__name__, 'ansible_plugins')

        if 'ansible_callback_facts_yaml' not in self.settings:
            self.settings['ansible_callback_facts_yaml'] = '{}/callback_facts.yaml'.format(self.settings['ansible_inventory_directory'])

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
            for required_fact in REQUIRED_FACTS:
                if not getattr(host, required_fact):
                    missing_facts.append(required_fact)
            if len(missing_facts) > 0:
                result[host.name] = missing_facts
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
            if host.name == name:
                return host
        return None
