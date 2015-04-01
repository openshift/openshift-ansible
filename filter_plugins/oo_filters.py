#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4

from ansible import errors, runner
import json
import pdb

def oo_pdb(arg):
    ''' This pops you into a pdb instance where arg is the data passed in from the filter.
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
    ''' This looks up dictionary attributes of the form a.b.c and returns the value.
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

    return [ item for sublist in data for item in sublist ]


def oo_collect(data, attribute=None, filters={}):
    ''' This takes a list of dict and collects all attributes specified into a list
        If filter is specified then we will include all items that match _ALL_ of filters.
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

    if filters:
        retval = [get_attr(d, attribute) for d in data if all([ d[key] == filters[key] for key in filters ]) ]
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
        raise errors.AnsibleFilterError("|failed expects to filter on a Dictionary")

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
        raise errors.AnsibleFilterError("|failed expects first param is a list of strings")
    retval = [prepend + s for s in data]
    return retval

class FilterModule (object):
    def filters(self):
        return {
                "oo_select_keys": oo_select_keys,
                "oo_collect": oo_collect,
                "oo_flatten": oo_flatten,
                "oo_len": oo_len,
                "oo_pdb": oo_pdb,
                "oo_prepend_strings_in_list": oo_prepend_strings_in_list
                }
