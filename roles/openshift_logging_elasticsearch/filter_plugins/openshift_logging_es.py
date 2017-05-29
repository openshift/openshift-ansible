'''
 Class providing lower bound filter to prevent users accidentally throttling their pods
'''
import re

def norm(x, m):
    x = x.strip(' ')
    match = re.search('([0-9\.]*)(.*)', x)
    val = match.group(1)
    unit = match.group(2).strip(' ')
    if unit not in m:
        raise ValueError('Unit ' + unit + ' not supported')
    return float(val) * m[unit]

def norm_cpu(x):
    m = {
        '':  1,
        'm': 1e-3
    }
    return norm(x, m)
    
def norm_mem(x):
    m = {
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
        '':  1,
    }
    return norm(x, m)

def lower_bound_cpu(x, limit):
    if not x:
        return x
    return max((norm_cpu(x), x), (norm_cpu(limit), limit))[1]

def lower_bound_mem(x, limit):
    if not x:
        return x
    return max((norm_mem(x), x), (norm_mem(limit), limit))[1]
    
class FilterModule(object):
    def filters(self):
        return {
            'lower_bound_cpu': lower_bound_cpu,
            'lower_bound_mem': lower_bound_mem
        }
