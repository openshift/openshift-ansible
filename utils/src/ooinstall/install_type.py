class InstallType(object):
    """
    An enumeration of the types and number of hosts required for recommended
    installations.
    """

    def __init__(self, name, restrictions):
        self.name = name
        self.masters = restrictions['masters']
        self.nodes = restrictions['nodes']
        self.storage = restrictions['storage']
        self.loadbalancer = restrictions['loadbalancer']

    def meets_requirements(self, install_type, oo_cfg):
        """
        Check if the given oo_cfg meets the named install_type.
        Used for checking config files passed through unattended
        installations.
        """
        hosts = oo_cfg.hosts
        try:
            install = SUPPORTED_INSTALL_TYPES.get(install_type)
        except KeyError:
            # Non-supported install type
            return

        num_masters = 0
        num_nodes = 0
        num_storage = 0
        num_lb = 0
        meets_req = True

        for host in hosts:
            if host.master:
                num_masters += 1
            if host.node:
                num_nodes += 1
            if host.storage:
                num_storage += 1
            if host.master_lb:
                num_lb += 1

        if num_masters < install.masters.lower or \
           num_masters > install.masters.upper:
            meets_req = False

        if num_nodes < install.nodes.lower or \
           num_nodes > install.nodes.upper:
            meets_req = False

        if num_storage < install.storage.lower or \
           num_storage > install.storage.upper:
            meets_req = False

        if num_lb < install.loadbalancer.lower or \
           num_lb > install.loadbalancer.upper:
            meets_req = False

        return meets_req


class HostRange(object):
    """
    An upper and lower limit for the number of a particular host type
    """
    INFINITY = 9999999

    def __init__(self, lower, upper):
        self.lower = lower
        self.upper = upper

    def in_range(self, number):
        return number >= self.lower and number <= self.upper


SUPPORTED_INSTALL_TYPES = {
    'all_in_one': InstallType('all_in_one',
                              {'masters':      HostRange(1, 1),
                               'nodes':        HostRange(1, 1),
                               'storage':      HostRange(1, 1),
                               'loadbalancer': HostRange(0, 0)}
                             ),
    'min_ha':     InstallType('min_ha',
                              {'masters':      HostRange(3, 3),
                               'nodes':        HostRange(3, 3),
                               'storage':      HostRange(1, 1),
                               'loadbalancer': HostRange(1, 1)}
                             ),
    'recommended_ha': InstallType('recommended_ha',
                                  {'masters':      HostRange(3, 3),
                                   'nodes':        HostRange(3, HostRange.INFINITY),
                                   'storage':      HostRange(1, 1),
                                   'loadbalancer': HostRange(1, 1)}
                                 ),
    'custom':         InstallType('custom',
                                  {'masters':      HostRange(1, HostRange.INFINITY),
                                   'nodes':        HostRange(1, HostRange.INFINITY),
                                   'storage':      HostRange(0, 1),
                                   'loadbalancer': HostRange(0, 1)}
                                 ),
}
