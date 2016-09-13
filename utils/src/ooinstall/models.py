# pylint: disable=too-few-public-methods,missing-docstring
"""
Models for the oo_config in memory object
"""


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
        dictionary = {}
        for prop in ['name', 'variables']:
            # If the property is defined (not None or False), export it:
            if getattr(self, prop):
                dictionary[prop] = getattr(self, prop)
        return dictionary


class InvalidHostError(Exception):
    """ Host in config is missing both ip and hostname. """
    pass


class Host(object):
    """ A system we will or have installed OpenShift on. """
    # pylint: disable=invalid-name,too-many-instance-attributes
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
            raise InvalidHostError(
                "You must specify either an ip or hostname as 'connect_to'")

    def __str__(self):
        return self.connect_to

    def __repr__(self):
        return self.connect_to

    def to_dict(self):
        """ Used when exporting to yaml. """
        dictionary = {}

        for prop in ['ip', 'hostname', 'public_ip', 'public_hostname', 'connect_to',
                     'preconfigured', 'containerized', 'schedulable', 'roles', 'node_labels', ]:
            # If the property is defined (not None or False), export it:
            if getattr(self, prop):
                dictionary[prop] = getattr(self, prop)
        for variable, value in self.other_variables.iteritems():
            dictionary[variable] = value

        return dictionary

    def is_master(self):
        return 'master' in self.roles

    def is_node(self):
        return 'node' in self.roles

    def is_master_lb(self):
        return 'master_lb' in self.roles

    def is_storage(self):
        return 'storage' in self.roles

    def is_etcd_member(self, all_hosts):
        """ Will this host be a member of a standalone etcd cluster. """
        if not self.is_master():
            return False
        masters = [host for host in all_hosts if host.is_master()]
        if len(masters) > 1:
            return True
        return False

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


class Deployment(object):
    def __init__(self, **kwargs):
        self.hosts = kwargs.get('hosts', [])
        self.roles = kwargs.get('roles', {})
        self.variables = kwargs.get('variables', {})

    # pylint: disable=no-self-use
    def to_dict(self):
        # TODO: write to_dict for Deployment
        return {}
