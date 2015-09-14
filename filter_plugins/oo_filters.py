#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4
'''
Custom filters for use in openshift-ansible
'''

from ansible import errors
from operator import itemgetter
import pdb
import re
import json


class FilterModule(object):
    ''' Custom ansible filters '''

    @staticmethod
    def oo_pdb(arg):
        ''' This pops you into a pdb instance where arg is the data passed in
            from the filter.
            Ex: "{{ hostvars | oo_pdb }}"
        '''
        pdb.set_trace()
        return arg

    @staticmethod
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

    @staticmethod
    def oo_flatten(data):
        ''' This filter plugin will flatten a list of lists
        '''
        if not issubclass(type(data), list):
            raise errors.AnsibleFilterError("|failed expects to flatten a List")

        return [item for sublist in data for item in sublist]

    @staticmethod
    def oo_collect(data, attribute=None, filters=None):
        ''' This takes a list of dict and collects all attributes specified into a
            list. If filter is specified then we will include all items that
            match _ALL_ of filters.  If a dict entry is missing the key in a
            filter it will be excluded from the match.
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
                raise errors.AnsibleFilterError("|failed expects filter to be a"
                                                " dict")
            retval = [FilterModule.get_attr(d, attribute) for d in data if (
                all([d.get(key, None) == filters[key] for key in filters]))]
        else:
            retval = [FilterModule.get_attr(d, attribute) for d in data]

        return retval

    @staticmethod
    def oo_select_keys_from_list(data, keys):
        ''' This returns a list, which contains the value portions for the keys
            Ex: data = { 'a':1, 'b':2, 'c':3 }
                keys = ['a', 'c']
                returns [1, 3]
        '''

        if not issubclass(type(data), list):
            raise errors.AnsibleFilterError("|failed expects to filter on a list")

        if not issubclass(type(keys), list):
            raise errors.AnsibleFilterError("|failed expects first param is a list")

        # Gather up the values for the list of keys passed in
        retval = [FilterModule.oo_select_keys(item, keys) for item in data]

        return FilterModule.oo_flatten(retval)

    @staticmethod
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
        retval = [data[key] for key in keys if data.has_key(key)]

        return retval

    @staticmethod
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

    @staticmethod
    def oo_combine_key_value(data, joiner='='):
        '''Take a list of dict in the form of { 'key': 'value'} and
           arrange them as a list of strings ['key=value']
        '''
        if not issubclass(type(data), list):
            raise errors.AnsibleFilterError("|failed expects first param is a list")

        rval = []
        for item in data:
            rval.append("%s%s%s" % (item['key'], joiner, item['value']))

        return rval

    @staticmethod
    def oo_combine_dict(data, in_joiner='=', out_joiner=' '):
        '''Take a dict in the form of { 'key': 'value', 'key': 'value' } and
           arrange them as a string 'key=value key=value'
        '''
        if not issubclass(type(data), dict):
            raise errors.AnsibleFilterError("|failed expects first param is a dict")

        return out_joiner.join([in_joiner.join([k, v]) for k, v in data.items()])

    @staticmethod
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

    @staticmethod
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
        if host_type not in ['master', 'node', 'etcd']:
            raise errors.AnsibleFilterError("|failed expects etcd, master or node"
                                            " as the host type")

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
        elif host_type == 'etcd':
            etcd_vol = data[host_type]['etcd']
            etcd_vol['device_name'] = '/dev/xvdb'
            etcd_vol['delete_on_termination'] = True
            if etcd_vol['device_type'] != 'io1':
                etcd_vol.pop('iops', None)
            return [root_vol, etcd_vol]
        return [root_vol]

    @staticmethod
    def oo_split(string, separator=','):
        ''' This splits the input string into a list
        '''
        return string.split(separator)

    @staticmethod
    def oo_filter_list(data, filter_attr=None):
        ''' This returns a list, which contains all items where filter_attr
            evaluates to true
            Ex: data = [ { a: 1, b: True },
                         { a: 3, b: False },
                         { a: 5, b: True } ]
                filter_attr = 'b'
                returns [ { a: 1, b: True },
                          { a: 5, b: True } ]
        '''
        if not issubclass(type(data), list):
            raise errors.AnsibleFilterError("|failed expects to filter on a list")

        if not issubclass(type(filter_attr), str):
            raise errors.AnsibleFilterError("|failed expects filter_attr is a str")

        # Gather up the values for the list of keys passed in
        return [x for x in data if x[filter_attr]]

    @staticmethod
    def oo_parse_heat_stack_outputs(data):
        ''' Formats the HEAT stack output into a usable form

            The goal is to transform something like this:

            +---------------+-------------------------------------------------+
            | Property      | Value                                           |
            +---------------+-------------------------------------------------+
            | capabilities  | [] |                                            |
            | creation_time | 2015-06-26T12:26:26Z |                          |
            | description   | OpenShift cluster |                             |
            | …             | …                                               |
            | outputs       | [                                               |
            |               |   {                                             |
            |               |     "output_value": "value_A"                   |
            |               |     "description": "This is the value of Key_A" |
            |               |     "output_key": "Key_A"                       |
            |               |   },                                            |
            |               |   {                                             |
            |               |     "output_value": [                           |
            |               |       "value_B1",                               |
            |               |       "value_B2"                                |
            |               |     ],                                          |
            |               |     "description": "This is the value of Key_B" |
            |               |     "output_key": "Key_B"                       |
            |               |   },                                            |
            |               | ]                                               |
            | parameters    | {                                               |
            | …             | …                                               |
            +---------------+-------------------------------------------------+

            into something like this:

            {
              "Key_A": "value_A",
              "Key_B": [
                "value_B1",
                "value_B2"
              ]
            }
        '''

        # Extract the “outputs” JSON snippet from the pretty-printed array
        in_outputs = False
        outputs = ''

        line_regex = re.compile(r'\|\s*(.*?)\s*\|\s*(.*?)\s*\|')
        for line in data['stdout_lines']:
            match = line_regex.match(line)
            if match:
                if match.group(1) == 'outputs':
                    in_outputs = True
                elif match.group(1) != '':
                    in_outputs = False
                if in_outputs:
                    outputs += match.group(2)

        outputs = json.loads(outputs)

        # Revamp the “outputs” to put it in the form of a “Key: value” map
        revamped_outputs = {}
        for output in outputs:
            revamped_outputs[output['output_key']] = output['output_value']

        return revamped_outputs

    def filters(self):
        ''' returns a mapping of filters to methods '''
        return {
            "oo_select_keys": self.oo_select_keys,
            "oo_select_keys_from_list": self.oo_select_keys_from_list,
            "oo_collect": self.oo_collect,
            "oo_flatten": self.oo_flatten,
            "oo_pdb": self.oo_pdb,
            "oo_prepend_strings_in_list": self.oo_prepend_strings_in_list,
            "oo_ami_selector": self.oo_ami_selector,
            "oo_ec2_volume_definition": self.oo_ec2_volume_definition,
            "oo_combine_key_value": self.oo_combine_key_value,
            "oo_combine_dict": self.oo_combine_dict,
            "oo_split": self.oo_split,
            "oo_filter_list": self.oo_filter_list,
            "oo_parse_heat_stack_outputs": self.oo_parse_heat_stack_outputs
        }
