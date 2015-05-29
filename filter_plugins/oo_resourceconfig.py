#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4
'''
Filters for configuring resources in openshift-ansible

Note: This file is a place holder for now until we can get these converted to
their own ansible module. Do not rely on anything in this file.
'''

from ansible import errors

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
        # HACK: If it is an array we are going to assume we want the first item
        if isinstance(ptr, list):
            ptr = ptr[0]
        ptr = ptr[attr]

    return ptr


def set_attr(item, key, value, attr_key=None, attr_value=None):
    ''' This creates an attribute with the passed in value.
        if the parent nodes are not present then it will create them

        Ex: set_attr({}, 'a.b.c.d', 25)
            returns {'a': {'b': {'c': {'d': 25}}}}
    '''
    if attr_key and attr_value:
        actual_attr_value = get_attr(item, attr_key)

        if str(attr_value) != str(actual_attr_value):
            # We only want to set the values on hosts with defined attributes
            return item

    kvp = item
    keyarray = key.split('.')
    keynum = 1
    for attr in keyarray:
        if keynum == len(keyarray):
            kvp[attr] = value
            return item
        else:
            if attr not in kvp:
                kvp[attr] = {}

            kvp = kvp[attr]
            keynum = keynum + 1

            if isinstance(kvp, (list, tuple)):
                set_attrs(kvp, '.'.join(keyarray[keynum-1::]), value)
                return item


def set_attrs(items, key, value, attr_key=None, attr_value=None):
    ''' Takes an array and runs set_attr on each item in the array
        using the specified key and value

        Ex: myitem={'a': 1, 'myarray': [{},{}]}
            set_attrs(myitem['myarray'], 'a', 25)
            returns [{'a': 25}, {'a': 25}]

        Even though it just returns the array, myitem will have the
        value of: {'a': 1, 'myarray': [{'a': 25}, {'a': 25}]}
    '''
    for item in items:
        set_attr(item, key, value, attr_key, attr_value)

    return items


def oo_set_node_region(arg, value, hosts):
    ''' Used to set the node's region

        Ex:
        - name: Get Nodes Config
          shell: osc get nodes -o json | sed -e '/"resourceVersion"/d'
          register: output

        - name: Get Node Lists
          set_fact:
            compute_hostvars: "{{ hostvars | oo_select_keys(groups['oo_nodes_to_config']) }}"

        - name: Set compute node regions
          set_fact:
            node_facts: "{{ output.stdout | from_json | oo_set_node_region(oln_node_region, compute_hostvars) }}"
    '''

    attr_key = 'status.addresses.address'

    for host in hosts:
        attr_value = str(host['openshift']['common']['ip'])
        set_attrs(arg['items'], 'metadata.labels.region', value, attr_key, attr_value)

    return arg

def oo_set_resource_node(arg, value):
    ''' This sets a deploymentConfig for a pod to deploy on specific
        nodes matching the value passed in.

        Ex:
        - shell: osc get deploymentConfig router -o json | sed -e '/"resourceVersion"/d'
          register: output

        - set_fact:
          router_deploymentconfig: "{{ output.stdout | from_json | oo_set_resource_node('infra') }}"
    '''
    set_attr(arg, 'template.podTemplate.nodeSelector.region', value)

    return arg

# disabling pylint checks for too-few-public-methods and no-self-use since we
# need to expose a FilterModule object that has a filters method that returns
# a mapping of filter names to methods.
# pylint: disable=too-few-public-methods, no-self-use
class FilterModule(object):
    ''' FilterModule '''
    def filters(self):
        ''' returns a mapping of filters to methods '''
        return {
            "oo_set_node_region": oo_set_node_region,
            "oo_set_resource_node": oo_set_resource_node
        }
