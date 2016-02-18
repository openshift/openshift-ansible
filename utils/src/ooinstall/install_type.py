# pylint: disable=bad-continuation,missing-docstring,no-self-use,invalid-name,too-many-instance-attributes,too-few-public-methods

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

def maximum_masters(install_type, num_masters):
    """
    Check if the given list of hosts has enough masters for the named install_type.
    Used for checking config files passed through unattended
    installations.
    """
    try:
        install = SUPPORTED_INSTALL_TYPES.get(install_type)
    except KeyError:
        # Non-supported install type
        return False

    return num_masters >= install.masters.upper



def meets_requirements(install_type, hosts):
    """
    Check if the given list of hosts meets the named install_type.
    Used for checking config files passed through unattended
    installations.
    """
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
        if host.is_master():
            num_masters += 1
        if host.is_node():
            num_nodes += 1
        if host.is_storage():
            num_storage += 1
        if host.is_master_lb():
            num_lb += 1

    if not install.masters.in_range(num_masters) or \
       not install.nodes.in_range(num_nodes) or \
       not install.storage.in_range(num_storage) or \
       not install.loadbalancer.in_range(num_lb):
        meets_req = False

    return meets_req


SUPPORTED_INSTALL_TYPES = {
    'all_in_one': InstallType('all_in_one',
                              {'masters':      HostRange(1, 1),
                               'nodes':        HostRange(1, 1),
                               'storage':      HostRange(0, 0),
                               'loadbalancer': HostRange(0, 0)}
                             ),
    'single_master': InstallType('min_ha',
                                 {'masters':      HostRange(1, 1),
                                  'nodes':        HostRange(1, HostRange.INFINITY),
                                  'storage':      HostRange(1, 1),
                                  'loadbalancer': HostRange(1, 1)}
                                ),
    'min_ha':     InstallType('min_ha',
                              {'masters':      HostRange(3, 3),
                               'nodes':        HostRange(3, 3),
                               'storage':      HostRange(1, 1),
                               'loadbalancer': HostRange(1, 1)}
                             ),
    'recommended_ha': InstallType('recommended_ha',
                                  {'masters':      HostRange(3, 3),
                                   'nodes':        HostRange(6, HostRange.INFINITY),
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
