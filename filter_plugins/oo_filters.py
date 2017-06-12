#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=too-many-lines
"""
Custom filters for use in openshift-ansible
"""
import json
import os
import pdb
import random
import re

from base64 import b64encode
from collections import Mapping
# pylint no-name-in-module and import-error disabled here because pylint
# fails to properly detect the packages when installed in a virtualenv
from distutils.util import strtobool  # pylint:disable=no-name-in-module,import-error
from distutils.version import LooseVersion  # pylint:disable=no-name-in-module,import-error
from operator import itemgetter

import pkg_resources
import yaml

from ansible import errors
from ansible.parsing.yaml.dumper import AnsibleDumper

# ansible.compat.six goes away with Ansible 2.4
try:
    from ansible.compat.six import string_types, u
    from ansible.compat.six.moves.urllib.parse import urlparse
except ImportError:
    from ansible.module_utils.six import string_types, u
    from ansible.module_utils.six.moves.urllib.parse import urlparse

HAS_OPENSSL = False
try:
    import OpenSSL.crypto
    HAS_OPENSSL = True
except ImportError:
    pass


def oo_pdb(arg):
    """ This pops you into a pdb instance where arg is the data passed in
        from the filter.
        Ex: "{{ hostvars | oo_pdb }}"
    """
    pdb.set_trace()
    return arg


def get_attr(data, attribute=None):
    """ This looks up dictionary attributes of the form a.b.c and returns
        the value.

        If the key isn't present, None is returned.
        Ex: data = {'a': {'b': {'c': 5}}}
            attribute = "a.b.c"
            returns 5
    """
    if not attribute:
        raise errors.AnsibleFilterError("|failed expects attribute to be set")

    ptr = data
    for attr in attribute.split('.'):
        if attr in ptr:
            ptr = ptr[attr]
        else:
            ptr = None
            break

    return ptr


def oo_flatten(data):
    """ This filter plugin will flatten a list of lists
    """
    if not isinstance(data, list):
        raise errors.AnsibleFilterError("|failed expects to flatten a List")

    return [item for sublist in data for item in sublist]


def oo_merge_dicts(first_dict, second_dict):
    """ Merge two dictionaries where second_dict values take precedence.
        Ex: first_dict={'a': 1, 'b': 2}
            second_dict={'b': 3, 'c': 4}
            returns {'a': 1, 'b': 3, 'c': 4}
    """
    if not isinstance(first_dict, dict) or not isinstance(second_dict, dict):
        raise errors.AnsibleFilterError("|failed expects to merge two dicts")
    merged = first_dict.copy()
    merged.update(second_dict)
    return merged


def oo_merge_hostvars(hostvars, variables, inventory_hostname):
    """ Merge host and play variables.

        When ansible version is greater than or equal to 2.0.0,
        merge hostvars[inventory_hostname] with variables (ansible vars)
        otherwise merge hostvars with hostvars['inventory_hostname'].

        Ex: hostvars={'master1.example.com': {'openshift_variable': '3'},
                      'openshift_other_variable': '7'}
            variables={'openshift_other_variable': '6'}
            inventory_hostname='master1.example.com'
            returns {'openshift_variable': '3', 'openshift_other_variable': '7'}

            hostvars=<ansible.vars.hostvars.HostVars object> (Mapping)
            variables={'openshift_other_variable': '6'}
            inventory_hostname='master1.example.com'
            returns {'openshift_variable': '3', 'openshift_other_variable': '6'}
    """
    if not isinstance(hostvars, Mapping):
        raise errors.AnsibleFilterError("|failed expects hostvars is dictionary or object")
    if not isinstance(variables, dict):
        raise errors.AnsibleFilterError("|failed expects variables is a dictionary")
    if not isinstance(inventory_hostname, string_types):
        raise errors.AnsibleFilterError("|failed expects inventory_hostname is a string")
    ansible_version = pkg_resources.get_distribution("ansible").version  # pylint: disable=maybe-no-member
    merged_hostvars = {}
    if LooseVersion(ansible_version) >= LooseVersion('2.0.0'):
        merged_hostvars = oo_merge_dicts(
            hostvars[inventory_hostname], variables)
    else:
        merged_hostvars = oo_merge_dicts(
            hostvars[inventory_hostname], hostvars)
    return merged_hostvars


def oo_collect(data_list, attribute=None, filters=None):
    """ This takes a list of dict and collects all attributes specified into a
        list. If filter is specified then we will include all items that
        match _ALL_ of filters.  If a dict entry is missing the key in a
        filter it will be excluded from the match.
        Ex: data_list = [ {'a':1, 'b':5, 'z': 'z'}, # True, return
                          {'a':2, 'z': 'z'},        # True, return
                          {'a':3, 'z': 'z'},        # True, return
                          {'a':4, 'z': 'b'},        # FAILED, obj['z'] != obj['z']
                        ]
            attribute = 'a'
            filters   = {'z': 'z'}
            returns [1, 2, 3]

        This also deals with lists of lists with dict as elements.
        Ex: data_list = [
                          [ {'a':1, 'b':5, 'z': 'z'}, # True, return
                            {'a':2, 'b':6, 'z': 'z'}  # True, return
                          ],
                          [ {'a':3, 'z': 'z'},        # True, return
                            {'a':4, 'z': 'b'}         # FAILED, obj['z'] != obj['z']
                          ],
                          {'a':5, 'z': 'z'},          # True, return
                        ]
            attribute = 'a'
            filters   = {'z': 'z'}
            returns [1, 2, 3, 5]
    """
    if not isinstance(data_list, list):
        raise errors.AnsibleFilterError("oo_collect expects to filter on a List")

    if not attribute:
        raise errors.AnsibleFilterError("oo_collect expects attribute to be set")

    data = []
    retval = []

    for item in data_list:
        if isinstance(item, list):
            retval.extend(oo_collect(item, attribute, filters))
        else:
            data.append(item)

    if filters is not None:
        if not isinstance(filters, dict):
            raise errors.AnsibleFilterError(
                "oo_collect expects filter to be a dict")
        retval.extend([get_attr(d, attribute) for d in data if (
            all([d.get(key, None) == filters[key] for key in filters]))])
    else:
        retval.extend([get_attr(d, attribute) for d in data])

    retval = [val for val in retval if val is not None]

    return retval


def oo_select_keys_from_list(data, keys):
    """ This returns a list, which contains the value portions for the keys
        Ex: data = { 'a':1, 'b':2, 'c':3 }
            keys = ['a', 'c']
            returns [1, 3]
    """

    if not isinstance(data, list):
        raise errors.AnsibleFilterError("|failed expects to filter on a list")

    if not isinstance(keys, list):
        raise errors.AnsibleFilterError("|failed expects first param is a list")

    # Gather up the values for the list of keys passed in
    retval = [oo_select_keys(item, keys) for item in data]

    return oo_flatten(retval)


def oo_select_keys(data, keys):
    """ This returns a list, which contains the value portions for the keys
        Ex: data = { 'a':1, 'b':2, 'c':3 }
            keys = ['a', 'c']
            returns [1, 3]
    """

    if not isinstance(data, Mapping):
        raise errors.AnsibleFilterError("|failed expects to filter on a dict or object")

    if not isinstance(keys, list):
        raise errors.AnsibleFilterError("|failed expects first param is a list")

    # Gather up the values for the list of keys passed in
    retval = [data[key] for key in keys if key in data]

    return retval


def oo_prepend_strings_in_list(data, prepend):
    """ This takes a list of strings and prepends a string to each item in the
        list
        Ex: data = ['cart', 'tree']
            prepend = 'apple-'
            returns ['apple-cart', 'apple-tree']
    """
    if not isinstance(data, list):
        raise errors.AnsibleFilterError("|failed expects first param is a list")
    if not all(isinstance(x, string_types) for x in data):
        raise errors.AnsibleFilterError("|failed expects first param is a list"
                                        " of strings")
    retval = [prepend + s for s in data]
    return retval


def oo_combine_key_value(data, joiner='='):
    """Take a list of dict in the form of { 'key': 'value'} and
       arrange them as a list of strings ['key=value']
    """
    if not isinstance(data, list):
        raise errors.AnsibleFilterError("|failed expects first param is a list")

    rval = []
    for item in data:
        rval.append("%s%s%s" % (item['key'], joiner, item['value']))

    return rval


def oo_combine_dict(data, in_joiner='=', out_joiner=' '):
    """Take a dict in the form of { 'key': 'value', 'key': 'value' } and
       arrange them as a string 'key=value key=value'
    """
    if not isinstance(data, dict):
        # pylint: disable=line-too-long
        raise errors.AnsibleFilterError("|failed expects first param is a dict [oo_combine_dict]. Got %s. Type: %s" % (str(data), str(type(data))))

    return out_joiner.join([in_joiner.join([k, str(v)]) for k, v in data.items()])


def oo_dict_to_list_of_dict(data, key_title='key', value_title='value'):
    """Take a dict and arrange them as a list of dicts

       Input data:
       {'region': 'infra', 'test_k': 'test_v'}

       Return data:
       [{'key': 'region', 'value': 'infra'}, {'key': 'test_k', 'value': 'test_v'}]

       Written for use of the oc_label module
    """
    if not isinstance(data, dict):
        # pylint: disable=line-too-long
        raise errors.AnsibleFilterError("|failed expects first param is a dict. Got %s. Type: %s" % (str(data), str(type(data))))

    rval = []
    for label in data.items():
        rval.append({key_title: label[0], value_title: label[1]})

    return rval


def oo_ami_selector(data, image_name):
    """ This takes a list of amis and an image name and attempts to return
        the latest ami.
    """
    if not isinstance(data, list):
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
    """ This takes a dictionary of volume definitions and returns a valid ec2
        volume definition based on the host_type and the values in the
        dictionary.
        The dictionary should look similar to this:
            { 'master':
                { 'root':
                    { 'volume_size': 10, 'device_type': 'gp2',
                      'iops': 500
                    },
                    'docker':
                      { 'volume_size': 40, 'device_type': 'gp2',
                        'iops': 500, 'ephemeral': 'true'
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
    """
    if not isinstance(data, dict):
        # pylint: disable=line-too-long
        raise errors.AnsibleFilterError("|failed expects first param is a dict [oo_ec2_volume_def]. Got %s. Type: %s" % (str(data), str(type(data))))
    if host_type not in ['master', 'node', 'etcd']:
        raise errors.AnsibleFilterError("|failed expects etcd, master or node"
                                        " as the host type")

    root_vol = data[host_type]['root']
    root_vol['device_name'] = '/dev/sda1'
    root_vol['delete_on_termination'] = True
    if root_vol['device_type'] != 'io1':
        root_vol.pop('iops', None)
    if host_type in ['master', 'node'] and 'docker' in data[host_type]:
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
    elif host_type == 'etcd' and 'etcd' in data[host_type]:
        etcd_vol = data[host_type]['etcd']
        etcd_vol['device_name'] = '/dev/xvdb'
        etcd_vol['delete_on_termination'] = True
        if etcd_vol['device_type'] != 'io1':
            etcd_vol.pop('iops', None)
        return [root_vol, etcd_vol]
    return [root_vol]


def oo_split(string, separator=','):
    """ This splits the input string into a list. If the input string is
    already a list we will return it as is.
    """
    if isinstance(string, list):
        return string
    return string.split(separator)


def oo_haproxy_backend_masters(hosts, port):
    """ This takes an array of dicts and returns an array of dicts
        to be used as a backend for the haproxy role
    """
    servers = []
    for idx, host_info in enumerate(hosts):
        server = dict(name="master%s" % idx)
        server_ip = host_info['openshift']['common']['ip']
        server['address'] = "%s:%s" % (server_ip, port)
        server['opts'] = 'check'
        servers.append(server)
    return servers


def oo_filter_list(data, filter_attr=None):
    """ This returns a list, which contains all items where filter_attr
        evaluates to true
        Ex: data = [ { a: 1, b: True },
                     { a: 3, b: False },
                     { a: 5, b: True } ]
            filter_attr = 'b'
            returns [ { a: 1, b: True },
                      { a: 5, b: True } ]
    """
    if not isinstance(data, list):
        raise errors.AnsibleFilterError("|failed expects to filter on a list")

    if not isinstance(filter_attr, string_types):
        raise errors.AnsibleFilterError("|failed expects filter_attr is a str or unicode")

    # Gather up the values for the list of keys passed in
    return [x for x in data if filter_attr in x and x[filter_attr]]


def oo_nodes_with_label(nodes, label, value=None):
    """ Filters a list of nodes by label and value (if provided)

        It handles labels that are in the following variables by priority:
        openshift_node_labels, cli_openshift_node_labels, openshift['node']['labels']

        Examples:
            data = ['a': {'openshift_node_labels': {'color': 'blue', 'size': 'M'}},
                    'b': {'openshift_node_labels': {'color': 'green', 'size': 'L'}},
                    'c': {'openshift_node_labels': {'size': 'S'}}]
            label = 'color'
            returns = ['a': {'openshift_node_labels': {'color': 'blue', 'size': 'M'}},
                       'b': {'openshift_node_labels': {'color': 'green', 'size': 'L'}}]

            data = ['a': {'openshift_node_labels': {'color': 'blue', 'size': 'M'}},
                    'b': {'openshift_node_labels': {'color': 'green', 'size': 'L'}},
                    'c': {'openshift_node_labels': {'size': 'S'}}]
            label = 'color'
            value = 'green'
            returns = ['b': {'labels': {'color': 'green', 'size': 'L'}}]

        Args:
            nodes (list[dict]): list of node to node variables
            label (str): label to filter `nodes` by
            value (Optional[str]): value of `label` to filter by Defaults
                                   to None.

        Returns:
            list[dict]: nodes filtered by label and value (if provided)
    """
    if not isinstance(nodes, list):
        raise errors.AnsibleFilterError("failed expects to filter on a list")
    if not isinstance(label, string_types):
        raise errors.AnsibleFilterError("failed expects label to be a string")
    if value is not None and not isinstance(value, string_types):
        raise errors.AnsibleFilterError("failed expects value to be a string")

    def label_filter(node):
        """ filter function for testing if node should be returned """
        if not isinstance(node, dict):
            raise errors.AnsibleFilterError("failed expects to filter on a list of dicts")
        if 'openshift_node_labels' in node:
            labels = node['openshift_node_labels']
        elif 'cli_openshift_node_labels' in node:
            labels = node['cli_openshift_node_labels']
        elif 'openshift' in node and 'node' in node['openshift'] and 'labels' in node['openshift']['node']:
            labels = node['openshift']['node']['labels']
        else:
            return False

        if isinstance(labels, string_types):
            labels = yaml.safe_load(labels)
        if not isinstance(labels, dict):
            raise errors.AnsibleFilterError(
                "failed expected node labels to be a dict or serializable to a dict"
            )
        return label in labels and (value is None or labels[label] == value)

    return [n for n in nodes if label_filter(n)]


def oo_parse_heat_stack_outputs(data):
    """ Formats the HEAT stack output into a usable form

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
    """

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


# pylint: disable=too-many-branches
def oo_parse_named_certificates(certificates, named_certs_dir, internal_hostnames):
    """ Parses names from list of certificate hashes.

        Ex: certificates = [{ "certfile": "/root/custom1.crt",
                              "keyfile": "/root/custom1.key",
                               "cafile": "/root/custom-ca1.crt" },
                            { "certfile": "custom2.crt",
                              "keyfile": "custom2.key",
                              "cafile": "custom-ca2.crt" }]

            returns [{ "certfile": "/etc/origin/master/named_certificates/custom1.crt",
                       "keyfile": "/etc/origin/master/named_certificates/custom1.key",
                       "cafile": "/etc/origin/master/named_certificates/custom-ca1.crt",
                       "names": [ "public-master-host.com",
                                  "other-master-host.com" ] },
                     { "certfile": "/etc/origin/master/named_certificates/custom2.crt",
                       "keyfile": "/etc/origin/master/named_certificates/custom2.key",
                       "cafile": "/etc/origin/master/named_certificates/custom-ca-2.crt",
                       "names": [ "some-hostname.com" ] }]
    """
    if not isinstance(named_certs_dir, string_types):
        raise errors.AnsibleFilterError("|failed expects named_certs_dir is str or unicode")

    if not isinstance(internal_hostnames, list):
        raise errors.AnsibleFilterError("|failed expects internal_hostnames is list")

    if not HAS_OPENSSL:
        raise errors.AnsibleFilterError("|missing OpenSSL python bindings")

    for certificate in certificates:
        if 'names' in certificate.keys():
            continue
        else:
            certificate['names'] = []

        if not os.path.isfile(certificate['certfile']) or not os.path.isfile(certificate['keyfile']):
            raise errors.AnsibleFilterError("|certificate and/or key does not exist '%s', '%s'" %
                                            (certificate['certfile'], certificate['keyfile']))

        try:
            st_cert = open(certificate['certfile'], 'rt').read()
            cert = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, st_cert)
            certificate['names'].append(str(cert.get_subject().commonName.decode()))
            for i in range(cert.get_extension_count()):
                if cert.get_extension(i).get_short_name() == 'subjectAltName':
                    for name in str(cert.get_extension(i)).replace('DNS:', '').split(', '):
                        certificate['names'].append(name)
        except Exception:
            raise errors.AnsibleFilterError(("|failed to parse certificate '%s', " % certificate['certfile'] +
                                             "please specify certificate names in host inventory"))

        certificate['names'] = list(set(certificate['names']))
        if 'cafile' not in certificate:
            certificate['names'] = [name for name in certificate['names'] if name not in internal_hostnames]
            if not certificate['names']:
                raise errors.AnsibleFilterError(("|failed to parse certificate '%s' or " % certificate['certfile'] +
                                                 "detected a collision with internal hostname, please specify " +
                                                 "certificate names in host inventory"))

    for certificate in certificates:
        # Update paths for configuration
        certificate['certfile'] = os.path.join(named_certs_dir, os.path.basename(certificate['certfile']))
        certificate['keyfile'] = os.path.join(named_certs_dir, os.path.basename(certificate['keyfile']))
        if 'cafile' in certificate:
            certificate['cafile'] = os.path.join(named_certs_dir, os.path.basename(certificate['cafile']))
    return certificates


def oo_pretty_print_cluster(data, prefix='tag_'):
    """ Read a subset of hostvars and build a summary of the cluster
        in the following layout:

"c_id": {
"master": {
"default": [
  { "name": "c_id-master-12345",       "public IP": "172.16.0.1", "private IP": "192.168.0.1" }
]
"node": {
"infra": [
  { "name": "c_id-node-infra-23456",   "public IP": "172.16.0.2", "private IP": "192.168.0.2" }
],
"compute": [
  { "name": "c_id-node-compute-23456", "public IP": "172.16.0.3", "private IP": "192.168.0.3" },
...
]
}
    """

    def _get_tag_value(tags, key):
        """ Extract values of a map implemented as a set.
            Ex: tags = { 'tag_foo_value1', 'tag_bar_value2', 'tag_baz_value3' }
                key = 'bar'
                returns 'value2'
        """
        for tag in tags:
            if tag[:len(prefix) + len(key)] == prefix + key:
                return tag[len(prefix) + len(key) + 1:]
        raise KeyError(key)

    def _add_host(clusters,
                  clusterid,
                  host_type,
                  sub_host_type,
                  host):
        """ Add a new host in the clusters data structure """
        if clusterid not in clusters:
            clusters[clusterid] = {}
        if host_type not in clusters[clusterid]:
            clusters[clusterid][host_type] = {}
        if sub_host_type not in clusters[clusterid][host_type]:
            clusters[clusterid][host_type][sub_host_type] = []
        clusters[clusterid][host_type][sub_host_type].append(host)

    clusters = {}
    for host in data:
        try:
            _add_host(clusters=clusters,
                      clusterid=_get_tag_value(host['group_names'], 'clusterid'),
                      host_type=_get_tag_value(host['group_names'], 'host-type'),
                      sub_host_type=_get_tag_value(host['group_names'], 'sub-host-type'),
                      host={'name': host['inventory_hostname'],
                            'public IP': host['oo_public_ipv4'],
                            'private IP': host['oo_private_ipv4']})
        except KeyError:
            pass
    return clusters


def oo_generate_secret(num_bytes):
    """ generate a session secret """

    if not isinstance(num_bytes, int):
        raise errors.AnsibleFilterError("|failed expects num_bytes is int")

    return b64encode(os.urandom(num_bytes)).decode('utf-8')


def to_padded_yaml(data, level=0, indent=2, **kw):
    """ returns a yaml snippet padded to match the indent level you specify """
    if data in [None, ""]:
        return ""

    try:
        transformed = u(yaml.dump(data, indent=indent, allow_unicode=True,
                                  default_flow_style=False,
                                  Dumper=AnsibleDumper, **kw))
        padded = "\n".join([" " * level * indent + line for line in transformed.splitlines()])
        return "\n{0}".format(padded)
    except Exception as my_e:
        raise errors.AnsibleFilterError('Failed to convert: %s' % my_e)


def oo_openshift_env(hostvars):
    ''' Return facts which begin with "openshift_" and translate
        legacy facts to their openshift_env counterparts.

        Ex: hostvars = {'openshift_fact': 42,
                        'theyre_taking_the_hobbits_to': 'isengard'}
            returns  = {'openshift_fact': 42}
    '''
    if not issubclass(type(hostvars), dict):
        raise errors.AnsibleFilterError("|failed expects hostvars is a dict")

    facts = {}
    regex = re.compile('^openshift_.*')
    for key in hostvars:
        if regex.match(key):
            facts[key] = hostvars[key]

    migrations = {'openshift_router_selector': 'openshift_hosted_router_selector',
                  'openshift_registry_selector': 'openshift_hosted_registry_selector'}
    for old_fact, new_fact in migrations.items():
        if old_fact in facts and new_fact not in facts:
            facts[new_fact] = facts[old_fact]
    return facts


# pylint: disable=too-many-branches, too-many-nested-blocks, too-many-statements
def oo_persistent_volumes(hostvars, groups, persistent_volumes=None):
    """ Generate list of persistent volumes based on oo_openshift_env
        storage options set in host variables.
    """
    if not issubclass(type(hostvars), dict):
        raise errors.AnsibleFilterError("|failed expects hostvars is a dict")
    if not issubclass(type(groups), dict):
        raise errors.AnsibleFilterError("|failed expects groups is a dict")
    if persistent_volumes is not None and not issubclass(type(persistent_volumes), list):
        raise errors.AnsibleFilterError("|failed expects persistent_volumes is a list")

    if persistent_volumes is None:
        persistent_volumes = []
    if 'hosted' in hostvars['openshift']:
        for component in hostvars['openshift']['hosted']:
            if 'storage' in hostvars['openshift']['hosted'][component]:
                params = hostvars['openshift']['hosted'][component]['storage']
                kind = params['kind']
                create_pv = params['create_pv']
                if kind is not None and create_pv:
                    if kind == 'nfs':
                        host = params['host']
                        if host is None:
                            if 'oo_nfs_to_config' in groups and len(groups['oo_nfs_to_config']) > 0:
                                host = groups['oo_nfs_to_config'][0]
                            else:
                                raise errors.AnsibleFilterError("|failed no storage host detected")
                        directory = params['nfs']['directory']
                        volume = params['volume']['name']
                        path = directory + '/' + volume
                        size = params['volume']['size']
                        if 'labels' in params:
                            labels = params['labels']
                        else:
                            labels = dict()
                        access_modes = params['access']['modes']
                        persistent_volume = dict(
                            name="{0}-volume".format(volume),
                            capacity=size,
                            labels=labels,
                            access_modes=access_modes,
                            storage=dict(
                                nfs=dict(
                                    server=host,
                                    path=path)))
                        persistent_volumes.append(persistent_volume)
                    elif kind == 'openstack':
                        volume = params['volume']['name']
                        size = params['volume']['size']
                        if 'labels' in params:
                            labels = params['labels']
                        else:
                            labels = dict()
                        access_modes = params['access']['modes']
                        filesystem = params['openstack']['filesystem']
                        volume_id = params['openstack']['volumeID']
                        persistent_volume = dict(
                            name="{0}-volume".format(volume),
                            capacity=size,
                            labels=labels,
                            access_modes=access_modes,
                            storage=dict(
                                cinder=dict(
                                    fsType=filesystem,
                                    volumeID=volume_id)))
                        persistent_volumes.append(persistent_volume)
                    elif kind == 'glusterfs':
                        volume = params['volume']['name']
                        size = params['volume']['size']
                        if 'labels' in params:
                            labels = params['labels']
                        else:
                            labels = dict()
                        access_modes = params['access']['modes']
                        endpoints = params['glusterfs']['endpoints']
                        path = params['glusterfs']['path']
                        read_only = params['glusterfs']['readOnly']
                        persistent_volume = dict(
                            name="{0}-volume".format(volume),
                            capacity=size,
                            labels=labels,
                            access_modes=access_modes,
                            storage=dict(
                                glusterfs=dict(
                                    endpoints=endpoints,
                                    path=path,
                                    readOnly=read_only)))
                        persistent_volumes.append(persistent_volume)
                    elif not (kind == 'object' or kind == 'dynamic'):
                        msg = "|failed invalid storage kind '{0}' for component '{1}'".format(
                            kind,
                            component)
                        raise errors.AnsibleFilterError(msg)
    return persistent_volumes


def oo_persistent_volume_claims(hostvars, persistent_volume_claims=None):
    """ Generate list of persistent volume claims based on oo_openshift_env
        storage options set in host variables.
    """
    if not issubclass(type(hostvars), dict):
        raise errors.AnsibleFilterError("|failed expects hostvars is a dict")
    if persistent_volume_claims is not None and not issubclass(type(persistent_volume_claims), list):
        raise errors.AnsibleFilterError("|failed expects persistent_volume_claims is a list")

    if persistent_volume_claims is None:
        persistent_volume_claims = []
    if 'hosted' in hostvars['openshift']:
        for component in hostvars['openshift']['hosted']:
            if 'storage' in hostvars['openshift']['hosted'][component]:
                params = hostvars['openshift']['hosted'][component]['storage']
                kind = params['kind']
                create_pv = params['create_pv']
                create_pvc = params['create_pvc']
                if kind not in [None, 'object'] and create_pv and create_pvc:
                    volume = params['volume']['name']
                    size = params['volume']['size']
                    access_modes = params['access']['modes']
                    persistent_volume_claim = dict(
                        name="{0}-claim".format(volume),
                        capacity=size,
                        access_modes=access_modes)
                    persistent_volume_claims.append(persistent_volume_claim)
    return persistent_volume_claims


def oo_31_rpm_rename_conversion(rpms, openshift_version=None):
    """ Filters a list of 3.0 rpms and return the corresponding 3.1 rpms
        names with proper version (if provided)

        If 3.1 rpms are passed in they will only be augmented with the
        correct version.  This is important for hosts that are running both
        Masters and Nodes.
    """
    if not isinstance(rpms, list):
        raise errors.AnsibleFilterError("failed expects to filter on a list")
    if openshift_version is not None and not isinstance(openshift_version, string_types):
        raise errors.AnsibleFilterError("failed expects openshift_version to be a string")

    rpms_31 = []
    for rpm in rpms:
        if 'atomic' not in rpm:
            rpm = rpm.replace("openshift", "atomic-openshift")
        if openshift_version:
            rpm = rpm + openshift_version
        rpms_31.append(rpm)

    return rpms_31


def oo_pods_match_component(pods, deployment_type, component):
    """ Filters a list of Pods and returns the ones matching the deployment_type and component
    """
    if not isinstance(pods, list):
        raise errors.AnsibleFilterError("failed expects to filter on a list")
    if not isinstance(deployment_type, string_types):
        raise errors.AnsibleFilterError("failed expects deployment_type to be a string")
    if not isinstance(component, string_types):
        raise errors.AnsibleFilterError("failed expects component to be a string")

    image_prefix = 'openshift/origin-'
    if deployment_type in ['enterprise', 'online', 'openshift-enterprise']:
        image_prefix = 'openshift3/ose-'
    elif deployment_type == 'atomic-enterprise':
        image_prefix = 'aep3_beta/aep-'

    matching_pods = []
    image_regex = image_prefix + component + r'.*'
    for pod in pods:
        for container in pod['spec']['containers']:
            if re.search(image_regex, container['image']):
                matching_pods.append(pod)
                break  # stop here, don't add a pod more than once

    return matching_pods


def oo_get_hosts_from_hostvars(hostvars, hosts):
    """ Return a list of hosts from hostvars """
    retval = []
    for host in hosts:
        try:
            retval.append(hostvars[host])
        except errors.AnsibleError:
            # host does not exist
            pass

    return retval


def oo_image_tag_to_rpm_version(version, include_dash=False):
    """ Convert an image tag string to an RPM version if necessary
        Empty strings and strings that are already in rpm version format
        are ignored. Also remove non semantic version components.

        Ex. v3.2.0.10 -> -3.2.0.10
            v1.2.0-rc1 -> -1.2.0
    """
    if not isinstance(version, string_types):
        raise errors.AnsibleFilterError("|failed expects a string or unicode")
    if version.startswith("v"):
        version = version[1:]
        # Strip release from requested version, we no longer support this.
        version = version.split('-')[0]

    if include_dash and version and not version.startswith("-"):
        version = "-" + version

    return version


def oo_hostname_from_url(url):
    """ Returns the hostname contained in a URL

        Ex: https://ose3-master.example.com/v1/api -> ose3-master.example.com
    """
    if not isinstance(url, string_types):
        raise errors.AnsibleFilterError("|failed expects a string or unicode")
    parse_result = urlparse(url)
    if parse_result.netloc != '':
        return parse_result.netloc
    else:
        # netloc wasn't parsed, assume url was missing scheme and path
        return parse_result.path


# pylint: disable=invalid-name, unused-argument
def oo_openshift_loadbalancer_frontends(
        api_port, servers_hostvars, use_nuage=False, nuage_rest_port=None):
    """TODO: Document me."""
    loadbalancer_frontends = [{'name': 'atomic-openshift-api',
                               'mode': 'tcp',
                               'options': ['tcplog'],
                               'binds': ["*:{0}".format(api_port)],
                               'default_backend': 'atomic-openshift-api'}]
    if bool(strtobool(str(use_nuage))) and nuage_rest_port is not None:
        loadbalancer_frontends.append({'name': 'nuage-monitor',
                                       'mode': 'tcp',
                                       'options': ['tcplog'],
                                       'binds': ["*:{0}".format(nuage_rest_port)],
                                       'default_backend': 'nuage-monitor'})
    return loadbalancer_frontends


# pylint: disable=invalid-name
def oo_openshift_loadbalancer_backends(
        api_port, servers_hostvars, use_nuage=False, nuage_rest_port=None):
    """TODO: Document me."""
    loadbalancer_backends = [{'name': 'atomic-openshift-api',
                              'mode': 'tcp',
                              'option': 'tcplog',
                              'balance': 'source',
                              'servers': oo_haproxy_backend_masters(servers_hostvars, api_port)}]
    if bool(strtobool(str(use_nuage))) and nuage_rest_port is not None:
        # pylint: disable=line-too-long
        loadbalancer_backends.append({'name': 'nuage-monitor',
                                      'mode': 'tcp',
                                      'option': 'tcplog',
                                      'balance': 'source',
                                      'servers': oo_haproxy_backend_masters(servers_hostvars, nuage_rest_port)})
    return loadbalancer_backends


def oo_chomp_commit_offset(version):
    """Chomp any "+git.foo" commit offset string from the given `version`
    and return the modified version string.

Ex:
- chomp_commit_offset(None)                 => None
- chomp_commit_offset(1337)                 => "1337"
- chomp_commit_offset("v3.4.0.15+git.derp") => "v3.4.0.15"
- chomp_commit_offset("v3.4.0.15")          => "v3.4.0.15"
- chomp_commit_offset("v1.3.0+52492b4")     => "v1.3.0"
    """
    if version is None:
        return version
    else:
        # Stringify, just in case it's a Number type. Split by '+' and
        # return the first split. No concerns about strings without a
        # '+', .split() returns an array of the original string.
        return str(version).split('+')[0]


def oo_random_word(length, source='abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'):
    """Generates a random string of given length from a set of alphanumeric characters.
       The default source uses [a-z][A-Z][0-9]
       Ex:
       - oo_random_word(3)                => aB9
       - oo_random_word(4, source='012')  => 0123
    """
    return ''.join(random.choice(source) for i in range(length))


class FilterModule(object):
    """ Custom ansible filter mapping """

    # pylint: disable=no-self-use, too-few-public-methods
    def filters(self):
        """ returns a mapping of filters to methods """
        return {
            "oo_select_keys": oo_select_keys,
            "oo_select_keys_from_list": oo_select_keys_from_list,
            "oo_chomp_commit_offset": oo_chomp_commit_offset,
            "oo_collect": oo_collect,
            "oo_flatten": oo_flatten,
            "oo_pdb": oo_pdb,
            "oo_prepend_strings_in_list": oo_prepend_strings_in_list,
            "oo_ami_selector": oo_ami_selector,
            "oo_ec2_volume_definition": oo_ec2_volume_definition,
            "oo_combine_key_value": oo_combine_key_value,
            "oo_combine_dict": oo_combine_dict,
            "oo_dict_to_list_of_dict": oo_dict_to_list_of_dict,
            "oo_split": oo_split,
            "oo_filter_list": oo_filter_list,
            "oo_parse_heat_stack_outputs": oo_parse_heat_stack_outputs,
            "oo_parse_named_certificates": oo_parse_named_certificates,
            "oo_haproxy_backend_masters": oo_haproxy_backend_masters,
            "oo_pretty_print_cluster": oo_pretty_print_cluster,
            "oo_generate_secret": oo_generate_secret,
            "oo_nodes_with_label": oo_nodes_with_label,
            "oo_openshift_env": oo_openshift_env,
            "oo_persistent_volumes": oo_persistent_volumes,
            "oo_persistent_volume_claims": oo_persistent_volume_claims,
            "oo_31_rpm_rename_conversion": oo_31_rpm_rename_conversion,
            "oo_pods_match_component": oo_pods_match_component,
            "oo_get_hosts_from_hostvars": oo_get_hosts_from_hostvars,
            "oo_image_tag_to_rpm_version": oo_image_tag_to_rpm_version,
            "oo_merge_dicts": oo_merge_dicts,
            "oo_hostname_from_url": oo_hostname_from_url,
            "oo_merge_hostvars": oo_merge_hostvars,
            "oo_openshift_loadbalancer_frontends": oo_openshift_loadbalancer_frontends,
            "oo_openshift_loadbalancer_backends": oo_openshift_loadbalancer_backends,
            "to_padded_yaml": to_padded_yaml,
            "oo_random_word": oo_random_word
        }
