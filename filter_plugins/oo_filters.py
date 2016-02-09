#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4
"""
Custom filters for use in openshift-ansible
"""

from ansible import errors
from operator import itemgetter
import OpenSSL.crypto
import os
import pdb
import re
import json
import yaml
from ansible.utils.unicode import to_unicode

# Disabling too-many-public-methods, since filter methods are necessarily
# public
# pylint: disable=too-many-public-methods
class FilterModule(object):
    """ Custom ansible filters """

    @staticmethod
    def oo_pdb(arg):
        """ This pops you into a pdb instance where arg is the data passed in
            from the filter.
            Ex: "{{ hostvars | oo_pdb }}"
        """
        pdb.set_trace()
        return arg

    @staticmethod
    def get_attr(data, attribute=None):
        """ This looks up dictionary attributes of the form a.b.c and returns
            the value.
            Ex: data = {'a': {'b': {'c': 5}}}
                attribute = "a.b.c"
                returns 5
        """
        if not attribute:
            raise errors.AnsibleFilterError("|failed expects attribute to be set")

        ptr = data
        for attr in attribute.split('.'):
            ptr = ptr[attr]

        return ptr

    @staticmethod
    def oo_flatten(data):
        """ This filter plugin will flatten a list of lists
        """
        if not isinstance(data, list):
            raise errors.AnsibleFilterError("|failed expects to flatten a List")

        return [item for sublist in data for item in sublist]

    @staticmethod
    def oo_collect(data, attribute=None, filters=None):
        """ This takes a list of dict and collects all attributes specified into a
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
        """
        if not isinstance(data, list):
            raise errors.AnsibleFilterError("|failed expects to filter on a List")

        if not attribute:
            raise errors.AnsibleFilterError("|failed expects attribute to be set")

        if filters is not None:
            if not isinstance(filters, dict):
                raise errors.AnsibleFilterError("|failed expects filter to be a"
                                                " dict")
            retval = [FilterModule.get_attr(d, attribute) for d in data if (
                all([d.get(key, None) == filters[key] for key in filters]))]
        else:
            retval = [FilterModule.get_attr(d, attribute) for d in data]

        return retval

    @staticmethod
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
        retval = [FilterModule.oo_select_keys(item, keys) for item in data]

        return FilterModule.oo_flatten(retval)

    @staticmethod
    def oo_select_keys(data, keys):
        """ This returns a list, which contains the value portions for the keys
            Ex: data = { 'a':1, 'b':2, 'c':3 }
                keys = ['a', 'c']
                returns [1, 3]
        """

        if not isinstance(data, dict):
            raise errors.AnsibleFilterError("|failed expects to filter on a dict")

        if not isinstance(keys, list):
            raise errors.AnsibleFilterError("|failed expects first param is a list")

        # Gather up the values for the list of keys passed in
        retval = [data[key] for key in keys if data.has_key(key)]

        return retval

    @staticmethod
    def oo_prepend_strings_in_list(data, prepend):
        """ This takes a list of strings and prepends a string to each item in the
            list
            Ex: data = ['cart', 'tree']
                prepend = 'apple-'
                returns ['apple-cart', 'apple-tree']
        """
        if not isinstance(data, list):
            raise errors.AnsibleFilterError("|failed expects first param is a list")
        if not all(isinstance(x, basestring) for x in data):
            raise errors.AnsibleFilterError("|failed expects first param is a list"
                                            " of strings")
        retval = [prepend + s for s in data]
        return retval

    @staticmethod
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

    @staticmethod
    def oo_combine_dict(data, in_joiner='=', out_joiner=' '):
        """Take a dict in the form of { 'key': 'value', 'key': 'value' } and
           arrange them as a string 'key=value key=value'
        """
        if not isinstance(data, dict):
            raise errors.AnsibleFilterError("|failed expects first param is a dict")

        return out_joiner.join([in_joiner.join([k, v]) for k, v in data.items()])

    @staticmethod
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

    @staticmethod
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
            raise errors.AnsibleFilterError("|failed expects first param is a dict")
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

    @staticmethod
    def oo_split(string, separator=','):
        """ This splits the input string into a list
        """
        return string.split(separator)

    @staticmethod
    def oo_haproxy_backend_masters(hosts):
        """ This takes an array of dicts and returns an array of dicts
            to be used as a backend for the haproxy role
        """
        servers = []
        for idx, host_info in enumerate(hosts):
            server = dict(name="master%s" % idx)
            server_ip = host_info['openshift']['common']['ip']
            server_port = host_info['openshift']['master']['api_port']
            server['address'] = "%s:%s" % (server_ip, server_port)
            server['opts'] = 'check'
            servers.append(server)
        return servers

    @staticmethod
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

        if not isinstance(filter_attr, basestring):
            raise errors.AnsibleFilterError("|failed expects filter_attr is a str or unicode")

        # Gather up the values for the list of keys passed in
        return [x for x in data if x.has_key(filter_attr) and x[filter_attr]]

    @staticmethod
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
        if not isinstance(label, basestring):
            raise errors.AnsibleFilterError("failed expects label to be a string")
        if value is not None and not isinstance(value, basestring):
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

            if isinstance(labels, basestring):
                labels = yaml.safe_load(labels)
            if not isinstance(labels, dict):
                raise errors.AnsibleFilterError(
                    "failed expected node labels to be a dict or serializable to a dict"
                )
            return label in labels and (value is None or labels[label] == value)

        return [n for n in nodes if label_filter(n)]


    @staticmethod
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

    @staticmethod
    # pylint: disable=too-many-branches
    def oo_parse_named_certificates(certificates, named_certs_dir, internal_hostnames):
        """ Parses names from list of certificate hashes.

            Ex: certificates = [{ "certfile": "/root/custom1.crt",
                                  "keyfile": "/root/custom1.key" },
                                { "certfile": "custom2.crt",
                                  "keyfile": "custom2.key" }]

                returns [{ "certfile": "/etc/origin/master/named_certificates/custom1.crt",
                           "keyfile": "/etc/origin/master/named_certificates/custom1.key",
                           "names": [ "public-master-host.com",
                                      "other-master-host.com" ] },
                         { "certfile": "/etc/origin/master/named_certificates/custom2.crt",
                           "keyfile": "/etc/origin/master/named_certificates/custom2.key",
                           "names": [ "some-hostname.com" ] }]
        """
        if not isinstance(named_certs_dir, basestring):
            raise errors.AnsibleFilterError("|failed expects named_certs_dir is str or unicode")

        if not isinstance(internal_hostnames, list):
            raise errors.AnsibleFilterError("|failed expects internal_hostnames is list")

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
            except:
                raise errors.AnsibleFilterError(("|failed to parse certificate '%s', " % certificate['certfile'] +
                                                 "please specify certificate names in host inventory"))

            certificate['names'] = [name for name in certificate['names'] if name not in internal_hostnames]
            certificate['names'] = list(set(certificate['names']))
            if not certificate['names']:
                raise errors.AnsibleFilterError(("|failed to parse certificate '%s' or " % certificate['certfile'] +
                                                 "detected a collision with internal hostname, please specify " +
                                                 "certificate names in host inventory"))

        for certificate in certificates:
            # Update paths for configuration
            certificate['certfile'] = os.path.join(named_certs_dir, os.path.basename(certificate['certfile']))
            certificate['keyfile'] = os.path.join(named_certs_dir, os.path.basename(certificate['keyfile']))
        return certificates

    @staticmethod
    def oo_pretty_print_cluster(data):
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
                if tag[:len(key)+4] == 'tag_' + key:
                    return tag[len(key)+5:]
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
                                'public IP': host['ansible_ssh_host'],
                                'private IP': host['ansible_default_ipv4']['address']})
            except KeyError:
                pass
        return clusters

    @staticmethod
    def oo_generate_secret(num_bytes):
        """ generate a session secret """

        if not isinstance(num_bytes, int):
            raise errors.AnsibleFilterError("|failed expects num_bytes is int")

        secret = os.urandom(num_bytes)
        return secret.encode('base-64').strip()

    @staticmethod
    def to_padded_yaml(data, level=0, indent=2, **kw):
        """ returns a yaml snippet padded to match the indent level you specify """
        if data in [None, ""]:
            return ""

        try:
            transformed = yaml.safe_dump(data, indent=indent, allow_unicode=True, default_flow_style=False, **kw)
            padded = "\n".join([" " * level * indent + line for line in transformed.splitlines()])
            return to_unicode("\n{0}".format(padded))
        except Exception as my_e:
            raise errors.AnsibleFilterError('Failed to convert: %s', my_e)

    @staticmethod
    def oo_openshift_env(hostvars):
        ''' Return facts which begin with "openshift_"
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
        return facts

    @staticmethod
    # pylint: disable=too-many-branches
    def oo_persistent_volumes(hostvars, groups, persistent_volumes=None):
        """ Generate list of persistent volumes based on oo_openshift_env
            storage options set in host variables.
        """
        if not issubclass(type(hostvars), dict):
            raise errors.AnsibleFilterError("|failed expects hostvars is a dict")
        if not issubclass(type(groups), dict):
            raise errors.AnsibleFilterError("|failed expects groups is a dict")
        if persistent_volumes != None and not issubclass(type(persistent_volumes), list):
            raise errors.AnsibleFilterError("|failed expects persistent_volumes is a list")

        if persistent_volumes == None:
            persistent_volumes = []
        for component in hostvars['openshift']['hosted']:
            kind = hostvars['openshift']['hosted'][component]['storage']['kind']
            create_pv = hostvars['openshift']['hosted'][component]['storage']['create_pv']
            if kind != None and create_pv:
                if kind == 'nfs':
                    host = hostvars['openshift']['hosted'][component]['storage']['host']
                    if host == None:
                        if len(groups['oo_nfs_to_config']) > 0:
                            host = groups['oo_nfs_to_config'][0]
                        else:
                            raise errors.AnsibleFilterError("|failed no storage host detected")
                    directory = hostvars['openshift']['hosted'][component]['storage']['nfs']['directory']
                    volume = hostvars['openshift']['hosted'][component]['storage']['volume']['name']
                    path = directory + '/' + volume
                    size = hostvars['openshift']['hosted'][component]['storage']['volume']['size']
                    access_modes = hostvars['openshift']['hosted'][component]['storage']['access_modes']
                    persistent_volume = dict(
                        name="{0}-volume".format(volume),
                        capacity=size,
                        access_modes=access_modes,
                        storage=dict(
                            nfs=dict(
                                server=host,
                                path=path)))
                    persistent_volumes.append(persistent_volume)
                else:
                    msg = "|failed invalid storage kind '{0}' for component '{1}'".format(
                        kind,
                        component)
                    raise errors.AnsibleFilterError(msg)
        return persistent_volumes

    @staticmethod
    def oo_persistent_volume_claims(hostvars, persistent_volume_claims=None):
        """ Generate list of persistent volume claims based on oo_openshift_env
            storage options set in host variables.
        """
        if not issubclass(type(hostvars), dict):
            raise errors.AnsibleFilterError("|failed expects hostvars is a dict")
        if persistent_volume_claims != None and not issubclass(type(persistent_volume_claims), list):
            raise errors.AnsibleFilterError("|failed expects persistent_volume_claims is a list")

        if persistent_volume_claims == None:
            persistent_volume_claims = []
        for component in hostvars['openshift']['hosted']:
            kind = hostvars['openshift']['hosted'][component]['storage']['kind']
            create_pv = hostvars['openshift']['hosted'][component]['storage']['create_pv']
            if kind != None and create_pv:
                volume = hostvars['openshift']['hosted'][component]['storage']['volume']['name']
                size = hostvars['openshift']['hosted'][component]['storage']['volume']['size']
                access_modes = hostvars['openshift']['hosted'][component]['storage']['access_modes']
                persistent_volume_claim = dict(
                    name="{0}-claim".format(volume),
                    capacity=size,
                    access_modes=access_modes)
                persistent_volume_claims.append(persistent_volume_claim)
        return persistent_volume_claims

    @staticmethod
    def oo_31_rpm_rename_conversion(rpms, openshift_version=None):
        """ Filters a list of 3.0 rpms and return the corresponding 3.1 rpms
            names with proper version (if provided)

            If 3.1 rpms are passed in they will only be augmented with the
            correct version.  This is important for hosts that are running both
            Masters and Nodes.
        """
        if not isinstance(rpms, list):
            raise errors.AnsibleFilterError("failed expects to filter on a list")
        if openshift_version is not None and not isinstance(openshift_version, basestring):
            raise errors.AnsibleFilterError("failed expects openshift_version to be a string")

        rpms_31 = []
        for rpm in rpms:
            if not 'atomic' in rpm:
                rpm = rpm.replace("openshift", "atomic-openshift")
            if openshift_version:
                rpm = rpm + openshift_version
            rpms_31.append(rpm)

        return rpms_31

    def filters(self):
        """ returns a mapping of filters to methods """
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
            "oo_parse_heat_stack_outputs": self.oo_parse_heat_stack_outputs,
            "oo_parse_named_certificates": self.oo_parse_named_certificates,
            "oo_haproxy_backend_masters": self.oo_haproxy_backend_masters,
            "oo_pretty_print_cluster": self.oo_pretty_print_cluster,
            "oo_generate_secret": self.oo_generate_secret,
            "to_padded_yaml": self.to_padded_yaml,
            "oo_nodes_with_label": self.oo_nodes_with_label,
            "oo_openshift_env": self.oo_openshift_env,
            "oo_persistent_volumes": self.oo_persistent_volumes,
            "oo_persistent_volume_claims": self.oo_persistent_volume_claims,
            "oo_31_rpm_rename_conversion": self.oo_31_rpm_rename_conversion,
        }
