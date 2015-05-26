#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4
'''
Filters for configuring resources in openshift-ansible
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

            ''' This is for handling cases where one of the subkeys
                is an array.

                Ex:
                set_attr({'a':{'b':[{'c':{}},{'c':{}}]}}, 'a.b.c', 25)
                returns {'a': {'b': [{'c': 25}, {'c': 25}]}}
            '''
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


def oo_set_node_label(arg, key, value, attr_key=None, attr_value=None):
    ''' This cycles through openshift node definitions
        (from "osc get nodes -o json"), and adds a label.

        If attr_key and attr_value are set, this will only set the label on
        nodes where the attribute matches the specified value.

        Ex:
        - shell: osc get nodes -o json | sed -e '/"resourceVersion"/d'
          register: output

        - set_fact:
          node_facts: "{{ output.stdout
                             | from_json
                             | oo_set_node_label('region', 'infra',
                                            'metadata.name', '172.16.17.43') }}"
    '''
    set_attrs(arg['items'], 'metadata.labels.'+key, value, attr_key, attr_value)

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


class FilterModule(object):
    ''' FilterModule '''
    def filters(self):
        ''' returns a mapping of filters to methods '''
        return {
            "oo_set_node_label": oo_set_node_label,
            "oo_set_resource_node": oo_set_resource_node
        }
