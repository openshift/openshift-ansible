#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4
'''
Custom filters for use in openshift-ansible
'''

from ansible import errors
from operator import itemgetter
import pdb

def oo_pdb(arg):
    ''' This pops you into a pdb instance where arg is the data passed in
        from the filter.
        Ex: "{{ hostvars | oo_pdb }}"
    '''
    pdb.set_trace()
    return arg

def oo_len(arg):
    ''' This returns the length of the argument
        Ex: "{{ hostvars | oo_len }}"
    '''
    return len(arg)

def get_attr(data, attribute=None):
    ''' This looks up dictionary attributes of the form a.b.c and returns
        the value.
        Ex: data = {'a': {'b': {'c': 5}}}
            attribute = "a.b.c"
            returns 5
    '''
    if not attribute:
        raise errors.AnsibleFilterError("|failed expects attribute to be set")

    ptr = data
    for attr in attribute.split('.'):
        ptr = ptr[attr]

    return ptr

def oo_flatten(data):
    ''' This filter plugin will flatten a list of lists
    '''
    if not issubclass(type(data), list):
        raise errors.AnsibleFilterError("|failed expects to flatten a List")

    return [item for sublist in data for item in sublist]


def oo_collect(data, attribute=None, filters=None):
    ''' This takes a list of dict and collects all attributes specified into a
        list If filter is specified then we will include all items that match
        _ALL_ of filters.
        Ex: data = [ {'a':1, 'b':5, 'z': 'z'}, # True, return
                     {'a':2, 'z': 'z'},        # True, return
                     {'a':3, 'z': 'z'},        # True, return
                     {'a':4, 'z': 'b'},        # FAILED, obj['z'] != obj['z']
                   ]
            attribute = 'a'
            filters   = {'z': 'z'}
            returns [1, 2, 3]
    '''
    if not issubclass(type(data), list):
        raise errors.AnsibleFilterError("|failed expects to filter on a List")

    if not attribute:
        raise errors.AnsibleFilterError("|failed expects attribute to be set")

    if filters is not None:
        if not issubclass(type(filters), dict):
            raise errors.AnsibleFilterError("|fialed expects filter to be a"
                                            " dict")
        retval = [get_attr(d, attribute) for d in data if (
            all([d[key] == filters[key] for key in filters]))]
    else:
        retval = [get_attr(d, attribute) for d in data]

    return retval

def oo_select_keys(data, keys):
    ''' This returns a list, which contains the value portions for the keys
        Ex: data = { 'a':1, 'b':2, 'c':3 }
            keys = ['a', 'c']
            returns [1, 3]
    '''

    if not issubclass(type(data), dict):
        raise errors.AnsibleFilterError("|failed expects to filter on a dict")

    if not issubclass(type(keys), list):
        raise errors.AnsibleFilterError("|failed expects first param is a list")

    # Gather up the values for the list of keys passed in
    retval = [data[key] for key in keys]

    return retval

def oo_prepend_strings_in_list(data, prepend):
    ''' This takes a list of strings and prepends a string to each item in the
        list
        Ex: data = ['cart', 'tree']
            prepend = 'apple-'
            returns ['apple-cart', 'apple-tree']
    '''
    if not issubclass(type(data), list):
        raise errors.AnsibleFilterError("|failed expects first param is a list")
    if not all(isinstance(x, basestring) for x in data):
        raise errors.AnsibleFilterError("|failed expects first param is a list"
                                        " of strings")
    retval = [prepend + s for s in data]
    return retval

def oo_ami_selector(data, image_name):
    ''' This takes a list of amis and an image name and attempts to return
        the latest ami.
    '''
    if not issubclass(type(data), list):
        raise errors.AnsibleFilterError("|failed expects first param is a list")

    if not data:
        return None
    else:
        if image_name is None or not image_name.endswith('_*'):
            ami = sorted(data, key=itemgetter('name'), reverse=True)[0]
            return ami['ami_id']
        else:
            ami_info = [(ami, ami['name'].split('_')[-1]) for ami in data]
            ami = sorted(ami_info, key=itemgetter(1), reverse=True)[0][0]
            return ami['ami_id']

def oo_ec2_volume_definition(data, host_type, docker_ephemeral=False):
    ''' This takes a dictionary of volume definitions and returns a valid ec2
        volume definition based on the host_type and the values in the
        dictionary.
        The dictionary should look similar to this:
            { 'master':
                { 'root':
                    { 'volume_size': 10, 'device_type': 'gp2',
                      'iops': 500
                    }
                },
              'node':
                { 'root':
                    { 'volume_size': 10, 'device_type': 'io1',
                      'iops': 1000
                    },
                  'docker':
                    { 'volume_size': 40, 'device_type': 'gp2',
                      'iops': 500, 'ephemeral': 'true'
                    }
                }
            }
    '''
    if not issubclass(type(data), dict):
        raise errors.AnsibleFilterError("|failed expects first param is a dict")
    if host_type not in ['master', 'node']:
        raise errors.AnsibleFilterError("|failed expects either master or node"
                                        " host type")

    root_vol = data[host_type]['root']
    root_vol['device_name'] = '/dev/sda1'
    root_vol['delete_on_termination'] = True
    if root_vol['device_type'] != 'io1':
        root_vol.pop('iops', None)
    if host_type == 'node':
        docker_vol = data[host_type]['docker']
        docker_vol['device_name'] = '/dev/xvdb'
        docker_vol['delete_on_termination'] = True
        if docker_vol['device_type'] != 'io1':
            docker_vol.pop('iops', None)
        if docker_ephemeral:
            docker_vol.pop('device_type', None)
            docker_vol.pop('delete_on_termination', None)
            docker_vol['ephemeral'] = 'ephemeral0'
        return [root_vol, docker_vol]
    return [root_vol]

# disabling pylint checks for too-few-public-methods and no-self-use since we
# need to expose a FilterModule object that has a filters method that returns
# a mapping of filter names to methods.
# pylint: disable=too-few-public-methods, no-self-use
class FilterModule(object):
    ''' FilterModule '''
    def filters(self):
        ''' returns a mapping of filters to methods '''
        return {
            "oo_select_keys": oo_select_keys,
            "oo_collect": oo_collect,
            "oo_flatten": oo_flatten,
            "oo_len": oo_len,
            "oo_pdb": oo_pdb,
            "oo_prepend_strings_in_list": oo_prepend_strings_in_list,
            "oo_ami_selector": oo_ami_selector,
            "oo_ec2_volume_definition": oo_ec2_volume_definition
        }
