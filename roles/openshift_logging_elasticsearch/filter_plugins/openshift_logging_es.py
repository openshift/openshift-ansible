'''
 Class providing lower bound filter to prevent users accidentally throttling their pods
'''

import re


def norm(value, prefix_map):
    '''Normalize value based on the prefix_map'''
    value = value.strip(' ')
    match = re.search('([0-9.]*)(.*)', value)
    val = match.group(1)
    unit = match.group(2).strip(' ')
    if unit not in prefix_map:
        raise ValueError('Unit ' + unit + ' not supported')
    return float(val) * prefix_map[unit]


def norm_cpu(value):
    '''Normalize cpu value'''
    prefix_map = {
        '': 1,
        'm': 1e-3
    }
    return norm(value, prefix_map)


def norm_mem(value):
    '''Normalize memory value'''
    prefix_map = {
        'E': 1e18,
        'P': 1e15,
        'T': 1e12,
        'G': 1e9,
        'M': 1e6,
        'K': 1e3,
        'Ei': 1e18,
        'Pi': 1e15,
        'Ti': 1e12,
        'Gi': 1e9,
        'Mi': 1e6,
        'Ki': 1e3,
        '': 1,
    }
    return norm(value, prefix_map)


def lower_bound_cpu(value, limit):
    '''Set return max(value, limit) respecting the unit conversions'''
    if not value:
        return value
    return max((norm_cpu(value), value), (norm_cpu(limit), limit))[1]


def lower_bound_mem(value, limit):
    '''Set return max(value, limit) respecting the unit conversions'''
    if not value:
        return value
    return max((norm_mem(value), value), (norm_mem(limit), limit))[1]


# pylint: disable=too-few-public-methods
class FilterModule(object):
    ''' OpenShift Logging Filters for ES '''

    # pylint: disable=no-self-use, too-few-public-methods
    def filters(self):
        ''' Returns the names of the filters provided by this class '''
        return {
            'lower_bound_cpu': lower_bound_cpu,
            'lower_bound_mem': lower_bound_mem
        }
