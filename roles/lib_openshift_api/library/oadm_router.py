#!/usr/bin/env python
#     ___ ___ _  _ ___ ___    _ _____ ___ ___
#    / __| __| \| | __| _ \  /_\_   _| __|   \
#   | (_ | _|| .` | _||   / / _ \| | | _|| |) |
#    \___|___|_|\_|___|_|_\/_/_\_\_|_|___|___/_ _____
#   |   \ / _ \  | \| |/ _ \_   _| | __|   \_ _|_   _|
#   | |) | (_) | | .` | (_) || |   | _|| |) | |  | |
#   |___/ \___/  |_|\_|\___/ |_|   |___|___/___| |_|
'''
   OpenShiftCLI class that wraps the oc commands in a subprocess
'''

import atexit
import json
import os
import shutil
import subprocess
import re

import yaml
# This is here because of a bug that causes yaml
# to incorrectly handle timezone info on timestamps
def timestamp_constructor(_, node):
    '''return timestamps as strings'''
    return str(node.value)
yaml.add_constructor(u'tag:yaml.org,2002:timestamp', timestamp_constructor)

# pylint: disable=too-few-public-methods
class OpenShiftCLI(object):
    ''' Class to wrap the command line tools '''
    def __init__(self,
                 namespace,
                 kubeconfig='/etc/origin/master/admin.kubeconfig',
                 verbose=False):
        ''' Constructor for OpenshiftCLI '''
        self.namespace = namespace
        self.verbose = verbose
        self.kubeconfig = kubeconfig

    # Pylint allows only 5 arguments to be passed.
    # pylint: disable=too-many-arguments
    def _replace_content(self, resource, rname, content, force=False):
        ''' replace the current object with the content '''
        res = self._get(resource, rname)
        if not res['results']:
            return res

        fname = '/tmp/%s' % rname
        yed = Yedit(fname, res['results'][0])
        changes = []
        for key, value in content.items():
            changes.append(yed.put(key, value))

        if any([not change[0] for change in changes]):
            return {'returncode': 0, 'updated': False}

        yed.write()

        atexit.register(Utils.cleanup, [fname])

        return self._replace(fname, force)

    def _replace(self, fname, force=False):
        '''return all pods '''
        cmd = ['-n', self.namespace, 'replace', '-f', fname]
        if force:
            cmd.append('--force')
        return self.openshift_cmd(cmd)

    def _create(self, fname):
        '''return all pods '''
        return self.openshift_cmd(['create', '-f', fname, '-n', self.namespace])

    def _delete(self, resource, rname):
        '''return all pods '''
        return self.openshift_cmd(['delete', resource, rname, '-n', self.namespace])

    def _get(self, resource, rname=None):
        '''return a secret by name '''
        cmd = ['get', resource, '-o', 'json', '-n', self.namespace]
        if rname:
            cmd.append(rname)

        rval = self.openshift_cmd(cmd, output=True)

        # Ensure results are retuned in an array
        if rval.has_key('items'):
            rval['results'] = rval['items']
        elif not isinstance(rval['results'], list):
            rval['results'] = [rval['results']]

        return rval

    def openshift_cmd(self, cmd, oadm=False, output=False, output_type='json'):
        '''Base command for oc '''
        #cmds = ['/usr/bin/oc', '--config', self.kubeconfig]
        cmds = []
        if oadm:
            cmds = ['/usr/bin/oadm']
        else:
            cmds = ['/usr/bin/oc']

        cmds.extend(cmd)

        rval = {}
        results = ''
        err = None

        if self.verbose:
            print ' '.join(cmds)

        proc = subprocess.Popen(cmds,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env={'KUBECONFIG': self.kubeconfig})

        proc.wait()
        stdout = proc.stdout.read()
        stderr = proc.stderr.read()
        rval = {"returncode": proc.returncode,
                "results": results,
                "cmd": ' '.join(cmds),
               }

        if proc.returncode == 0:
            if output:
                if output_type == 'json':
                    try:
                        rval['results'] = json.loads(stdout)
                    except ValueError as err:
                        if "No JSON object could be decoded" in err.message:
                            err = err.message
                elif output_type == 'raw':
                    rval['results'] = stdout

            if self.verbose:
                print stdout
                print stderr
                print

            if err:
                rval.update({"err": err,
                             "stderr": stderr,
                             "stdout": stdout,
                             "cmd": cmds
                            })

        else:
            rval.update({"stderr": stderr,
                         "stdout": stdout,
                         "results": {},
                        })

        return rval

class Utils(object):
    ''' utilities for openshiftcli modules '''
    @staticmethod
    def create_file(rname, data, ftype=None):
        ''' create a file in tmp with name and contents'''
        path = os.path.join('/tmp', rname)
        with open(path, 'w') as fds:
            if ftype == 'yaml':
                fds.write(yaml.safe_dump(data, default_flow_style=False))

            elif ftype == 'json':
                fds.write(json.dumps(data))
            else:
                fds.write(data)

        # Register cleanup when module is done
        atexit.register(Utils.cleanup, [path])
        return path

    @staticmethod
    def create_files_from_contents(data):
        '''Turn an array of dict: filename, content into a files array'''
        files = []

        for sfile in data:
            path = Utils.create_file(sfile['path'], sfile['content'])
            files.append(path)

        return files

    @staticmethod
    def cleanup(files):
        '''Clean up on exit '''
        for sfile in files:
            if os.path.exists(sfile):
                if os.path.isdir(sfile):
                    shutil.rmtree(sfile)
                elif os.path.isfile(sfile):
                    os.remove(sfile)


    @staticmethod
    def exists(results, _name):
        ''' Check to see if the results include the name '''
        if not results:
            return False


        if Utils.find_result(results, _name):
            return True

        return False

    @staticmethod
    def find_result(results, _name):
        ''' Find the specified result by name'''
        rval = None
        for result in results:
            if result.has_key('metadata') and result['metadata']['name'] == _name:
                rval = result
                break

        return rval

    @staticmethod
    def get_resource_file(sfile, sfile_type='yaml'):
        ''' return the service file  '''
        contents = None
        with open(sfile) as sfd:
            contents = sfd.read()

        if sfile_type == 'yaml':
            contents = yaml.safe_load(contents)
        elif sfile_type == 'json':
            contents = json.loads(contents)

        return contents

    # Disabling too-many-branches.  This is a yaml dictionary comparison function
    # pylint: disable=too-many-branches,too-many-return-statements
    @staticmethod
    def check_def_equal(user_def, result_def, skip_keys=None, debug=False):
        ''' Given a user defined definition, compare it with the results given back by our query.  '''

        # Currently these values are autogenerated and we do not need to check them
        skip = ['metadata', 'status']
        if skip_keys:
            skip.extend(skip_keys)

        for key, value in result_def.items():
            if key in skip:
                continue

            # Both are lists
            if isinstance(value, list):
                if not isinstance(user_def[key], list):
                    if debug:
                        print 'user_def[key] is not a list'
                    return False

                for values in zip(user_def[key], value):
                    if isinstance(values[0], dict) and isinstance(values[1], dict):
                        if debug:
                            print 'sending list - list'
                            print type(values[0])
                            print type(values[1])
                        result = Utils.check_def_equal(values[0], values[1], skip_keys=skip_keys, debug=debug)
                        if not result:
                            print 'list compare returned false'
                            return False

                    elif value != user_def[key]:
                        if debug:
                            print 'value should be identical'
                            print value
                            print user_def[key]
                        return False

            # recurse on a dictionary
            elif isinstance(value, dict):
                if not isinstance(user_def[key], dict):
                    if debug:
                        print "dict returned false not instance of dict"
                    return False

                # before passing ensure keys match
                api_values = set(value.keys()) - set(skip)
                user_values = set(user_def[key].keys()) - set(skip)
                if api_values != user_values:
                    if debug:
                        print api_values
                        print user_values
                        print "keys are not equal in dict"
                    return False

                result = Utils.check_def_equal(user_def[key], value, skip_keys=skip_keys, debug=debug)
                if not result:
                    if debug:
                        print "dict returned false"
                        print result
                    return False

            # Verify each key, value pair is the same
            else:
                if not user_def.has_key(key) or value != user_def[key]:
                    if debug:
                        print "value not equal; user_def does not have key"
                        print value
                        print user_def[key]
                    return False

        return True

class YeditException(Exception):
    ''' Exception class for Yedit '''
    pass

class Yedit(object):
    ''' Class to modify yaml files '''
    re_valid_key = r"(((\[-?\d+\])|([a-zA-Z-./]+)).?)+$"
    re_key = r"(?:\[(-?\d+)\])|([a-zA-Z-./]+)"

    def __init__(self, filename=None, content=None, content_type='yaml'):
        self.content = content
        self.filename = filename
        self.__yaml_dict = content
        self.content_type = content_type
        if self.filename and not self.content:
            self.load(content_type=self.content_type)

    @property
    def yaml_dict(self):
        ''' getter method for yaml_dict '''
        return self.__yaml_dict

    @yaml_dict.setter
    def yaml_dict(self, value):
        ''' setter method for yaml_dict '''
        self.__yaml_dict = value

    @staticmethod
    def remove_entry(data, key):
        ''' remove data at location key '''
        if not (key and re.match(Yedit.re_valid_key, key) and isinstance(data, (list, dict))):
            return None

        key_indexes = re.findall(Yedit.re_key, key)
        for arr_ind, dict_key in key_indexes[:-1]:
            if dict_key and isinstance(data, dict):
                data = data.get(dict_key, None)
            elif arr_ind and isinstance(data, list) and int(arr_ind) <= len(data) - 1:
                data = data[int(arr_ind)]
            else:
                return None

        # process last index for remove
        # expected list entry
        if key_indexes[-1][0]:
            if isinstance(data, list) and int(key_indexes[-1][0]) <= len(data) - 1:
                del data[int(key_indexes[-1][0])]
                return True

        # expected dict entry
        elif key_indexes[-1][1]:
            if isinstance(data, dict):
                del data[key_indexes[-1][1]]
                return True

    @staticmethod
    def add_entry(data, key, item=None):
        ''' Get an item from a dictionary with key notation a.b.c
            d = {'a': {'b': 'c'}}}
            key = a.b
            return c
        '''
        if not (key and re.match(Yedit.re_valid_key, key) and isinstance(data, (list, dict))):
            return None

        curr_data = data

        key_indexes = re.findall(Yedit.re_key, key)
        for arr_ind, dict_key in key_indexes[:-1]:
            if dict_key:
                if isinstance(data, dict) and data.has_key(dict_key):
                    data = data[dict_key]
                    continue

                data[dict_key] = {}
                data = data[dict_key]

            elif arr_ind and isinstance(data, list) and int(arr_ind) <= len(data) - 1:
                data = data[int(arr_ind)]
            else:
                return None

        # process last index for add
        # expected list entry
        if key_indexes[-1][0] and isinstance(data, list) and int(key_indexes[-1][0]) <= len(data) - 1:
            data[int(key_indexes[-1][0])] = item

        # expected dict entry
        elif key_indexes[-1][1] and isinstance(data, dict):
            data[key_indexes[-1][1]] = item

        return curr_data

    @staticmethod
    def get_entry(data, key):
        ''' Get an item from a dictionary with key notation a.b.c
            d = {'a': {'b': 'c'}}}
            key = a.b
            return c
        '''
        if not (key and re.match(Yedit.re_valid_key, key) and isinstance(data, (list, dict))):
            return None

        key_indexes = re.findall(Yedit.re_key, key)
        for arr_ind, dict_key in key_indexes:
            if dict_key and isinstance(data, dict):
                data = data.get(dict_key, None)
            elif arr_ind and isinstance(data, list) and int(arr_ind) <= len(data) - 1:
                data = data[int(arr_ind)]
            else:
                return None

        return data

    def write(self):
        ''' write to file '''
        if not self.filename:
            raise YeditException('Please specify a filename.')

        with open(self.filename, 'w') as yfd:
            yfd.write(yaml.safe_dump(self.yaml_dict, default_flow_style=False))

    def read(self):
        ''' write to file '''
        # check if it exists
        if not self.exists():
            return None

        contents = None
        with open(self.filename) as yfd:
            contents = yfd.read()

        return contents

    def exists(self):
        ''' return whether file exists '''
        if os.path.exists(self.filename):
            return True

        return False

    def load(self, content_type='yaml'):
        ''' return yaml file '''
        contents = self.read()

        if not contents:
            return None

        # check if it is yaml
        try:
            if content_type == 'yaml':
                self.yaml_dict = yaml.load(contents)
            elif content_type == 'json':
                self.yaml_dict = json.loads(contents)
        except yaml.YAMLError as _:
            # Error loading yaml or json
            return None

        return self.yaml_dict

    def get(self, key):
        ''' get a specified key'''
        try:
            entry = Yedit.get_entry(self.yaml_dict, key)
        except KeyError as _:
            entry = None

        return entry

    def delete(self, key):
        ''' remove key from a dict'''
        try:
            entry = Yedit.get_entry(self.yaml_dict, key)
        except KeyError as _:
            entry = None
        if not entry:
            return  (False, self.yaml_dict)

        result = Yedit.remove_entry(self.yaml_dict, key)
        if not result:
            return (False, self.yaml_dict)

        return (True, self.yaml_dict)

    def put(self, key, value):
        ''' put key, value into a dict '''
        try:
            entry = Yedit.get_entry(self.yaml_dict, key)
        except KeyError as _:
            entry = None

        if entry == value:
            return (False, self.yaml_dict)

        result = Yedit.add_entry(self.yaml_dict, key, value)
        if not result:
            return (False, self.yaml_dict)

        return (True, self.yaml_dict)

    def create(self, key, value):
        ''' create a yaml file '''
        if not self.exists():
            self.yaml_dict = {key: value}
            return (True, self.yaml_dict)

        return (False, self.yaml_dict)

import time

class RouterConfig(object):
    ''' RouterConfig is a DTO for the router.  '''
    def __init__(self, rname, kubeconfig, router_options):
        self.name = rname
        self.kubeconfig = kubeconfig
        self._router_options = router_options

    @property
    def router_options(self):
        ''' return router options '''
        return self._router_options

    def to_option_list(self):
        ''' return all options as a string'''
        return RouterConfig.stringify(self.router_options)

    @staticmethod
    def stringify(options):
        ''' return hash as list of key value pairs '''
        rval = []
        for key, data in options.items():
            if data['include'] and data['value']:
                rval.append('--%s=%s' % (key.replace('_', '-'), data['value']))

        return rval

class Router(OpenShiftCLI):
    ''' Class to wrap the oc command line tools '''
    def __init__(self,
                 router_config,
                 verbose=False):
        ''' Constructor for OpenshiftOC

           a router consists of 3 or more parts
           - dc/router
           - svc/router
           - endpoint/router
        '''
        super(Router, self).__init__('default', router_config.kubeconfig, verbose)
        self.rconfig = router_config
        self.verbose = verbose
        self.router_parts = [{'kind': 'dc', 'name': self.rconfig.name},
                             {'kind': 'svc', 'name': self.rconfig.name},
                             #{'kind': 'endpoints', 'name': self.rconfig.name},
                            ]
    def get(self, filter_kind=None):
        ''' return the self.router_parts '''
        rparts = self.router_parts
        parts = []
        if filter_kind:
            rparts = [part for part in self.router_parts if filter_kind == part['kind']]

        for part in rparts:
            parts.append(self._get(part['kind'], rname=part['name']))

        return parts

    def exists(self):
        '''return a deploymentconfig by name '''
        parts = self.get()
        for part in parts:
            if part['returncode'] != 0:
                return False

        return True

    def delete(self):
        '''return all pods '''
        parts = []
        for part in self.router_parts:
            parts.append(self._delete(part['kind'], part['name']))

        return parts

    def create(self, dryrun=False, output=False, output_type='json'):
        '''Create a deploymentconfig '''
        # We need to create the pem file
        router_pem = '/tmp/router.pem'
        with open(router_pem, 'w') as rfd:
            rfd.write(open(self.rconfig.router_options['cert_file']['value']).read())
            rfd.write(open(self.rconfig.router_options['key_file']['value']).read())

        atexit.register(Utils.cleanup, [router_pem])
        self.rconfig.router_options['default_cert']['value'] = router_pem

        options = self.rconfig.to_option_list()

        cmd = ['router']
        cmd.extend(options)
        if dryrun:
            cmd.extend(['--dry-run=True', '-o', 'json'])

        results = self.openshift_cmd(cmd, oadm=True, output=output, output_type=output_type)

        return results

    def update(self):
        '''run update for the router.  This performs a delete and then create '''
        parts = self.delete()
        if any([part['returncode'] != 0 for part in parts]):
            return parts

        # Ugly built in sleep here.
        time.sleep(15)

        return self.create()

    def needs_update(self, verbose=False):
        ''' check to see if we need to update '''
        dc_inmem = self.get(filter_kind='dc')[0]
        if dc_inmem['returncode'] != 0:
            return dc_inmem

        user_dc = self.create(dryrun=True, output=True, output_type='raw')
        if user_dc['returncode'] != 0:
            return user_dc

        # Since the output from oadm_router is returned as raw
        # we need to parse it.  The first line is the stats_password
        user_dc_results = user_dc['results'].split('\n')
        # stats_password = user_dc_results[0]

        # Load the string back into json and get the newly created dc
        user_dc = json.loads('\n'.join(user_dc_results[1:]))['items'][0]

        # Router needs some exceptions.
        # We do not want to check the autogenerated password for stats admin
        if not self.rconfig.router_options['stats_password']['value']:
            for idx, env_var in enumerate(user_dc['spec']['template']['spec']['containers'][0]['env']):
                if env_var['name'] == 'STATS_PASSWORD':
                    env_var['value'] = \
                      dc_inmem['results'][0]['spec']['template']['spec']['containers'][0]['env'][idx]['value']

        # dry-run doesn't add the protocol to the ports section.  We will manually do that.
        for idx, port in enumerate(user_dc['spec']['template']['spec']['containers'][0]['ports']):
            if not port.has_key('protocol'):
                port['protocol'] = 'TCP'

        # These are different when generating
        skip = ['dnsPolicy',
                'terminationGracePeriodSeconds',
                'restartPolicy', 'timeoutSeconds',
                'livenessProbe', 'readinessProbe',
                'terminationMessagePath',
                'rollingParams',
               ]

        return not Utils.check_def_equal(user_dc, dc_inmem['results'][0], skip_keys=skip, debug=verbose)

def main():
    '''
    ansible oc module for secrets
    '''

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', type='str',
                       choices=['present', 'absent']),
            debug=dict(default=False, type='bool'),
            namespace=dict(default='default', type='str'),
            name=dict(default='router', type='str'),

            kubeconfig=dict(default='/etc/origin/master/admin.kubeconfig', type='str'),
            credentials=dict(default='/etc/origin/master/openshift-router.kubeconfig', type='str'),
            cert_file=dict(default=None, type='str'),
            key_file=dict(default=None, type='str'),
            image=dict(default=None, type='str'), #'openshift3/ose-${component}:${version}'
            latest_image=dict(default=False, type='bool'),
            labels=dict(default=None, type='list'),
            ports=dict(default=['80:80', '443:443'], type='list'),
            replicas=dict(default=1, type='int'),
            selector=dict(default=None, type='str'),
            service_account=dict(default='router', type='str'),
            router_type=dict(default='haproxy-router', type='str'),
            host_network=dict(default=True, type='bool'),
            # external host options
            external_host=dict(default=None, type='str'),
            external_host_vserver=dict(default=None, type='str'),
            external_host_insecure=dict(default=False, type='bool'),
            external_host_partition_path=dict(default=None, type='str'),
            external_host_username=dict(default=None, type='str'),
            external_host_password=dict(default=None, type='str'),
            external_host_private_key=dict(default=None, type='str'),
            # Metrics
            expose_metrics=dict(default=False, type='bool'),
            metrics_image=dict(default=None, type='str'),
            # Stats
            stats_user=dict(default=None, type='str'),
            stats_password=dict(default=None, type='str'),
            stats_port=dict(default=1936, type='int'),

        ),
        mutually_exclusive=[["router_type", "images"]],

        supports_check_mode=True,
    )

    rconfig = RouterConfig(module.params['name'],
                           module.params['kubeconfig'],
                           {'credentials': {'value': module.params['credentials'], 'include': True},
                            'default_cert': {'value': None, 'include': True},
                            'cert_file': {'value': module.params['cert_file'], 'include': False},
                            'key_file': {'value': module.params['key_file'], 'include': False},
                            'image': {'value': module.params['image'], 'include': True},
                            'latest_image': {'value': module.params['latest_image'], 'include': True},
                            'labels': {'value': module.params['labels'], 'include': True},
                            'ports': {'value': ','.join(module.params['ports']), 'include': True},
                            'replicas': {'value': module.params['replicas'], 'include': True},
                            'selector': {'value': module.params['selector'], 'include': True},
                            'service_account': {'value': module.params['service_account'], 'include': True},
                            'router_type': {'value': module.params['router_type'], 'include': False},
                            'host_network': {'value': module.params['host_network'], 'include': True},
                            'external_host': {'value': module.params['external_host'], 'include': True},
                            'external_host_vserver': {'value': module.params['external_host_vserver'],
                                                      'include': True},
                            'external_host_insecure': {'value': module.params['external_host_insecure'],
                                                       'include': True},
                            'external_host_partition_path': {'value': module.params['external_host_partition_path'],
                                                             'include': True},
                            'external_host_username': {'value': module.params['external_host_username'],
                                                       'include': True},
                            'external_host_password': {'value': module.params['external_host_password'],
                                                       'include': True},
                            'external_host_private_key': {'value': module.params['external_host_private_key'],
                                                          'include': True},
                            'expose_metrics': {'value': module.params['expose_metrics'], 'include': True},
                            'metrics_image': {'value': module.params['metrics_image'], 'include': True},
                            'stats_user': {'value': module.params['stats_user'], 'include': True},
                            'stats_password': {'value': module.params['stats_password'], 'include': True},
                            'stats_port': {'value': module.params['stats_port'], 'include': True},
                           })


    ocrouter = Router(rconfig)

    state = module.params['state']

    ########
    # Delete
    ########
    if state == 'absent':
        if not ocrouter.exists():
            module.exit_json(changed=False, state="absent")

        if module.check_mode:
            module.exit_json(change=False, msg='Would have performed a delete.')

        api_rval = ocrouter.delete()
        module.exit_json(changed=True, results=api_rval, state="absent")


    if state == 'present':
        ########
        # Create
        ########
        if not ocrouter.exists():

            if module.check_mode:
                module.exit_json(change=False, msg='Would have performed a create.')

            api_rval = ocrouter.create()

            module.exit_json(changed=True, results=api_rval, state="present")

        ########
        # Update
        ########
        if not ocrouter.needs_update():
            module.exit_json(changed=False, state="present")

        if module.check_mode:
            module.exit_json(change=False, msg='Would have performed an update.')

        api_rval = ocrouter.update()

        if api_rval['returncode'] != 0:
            module.fail_json(msg=api_rval)

        module.exit_json(changed=True, results=api_rval, state="present")

    module.exit_json(failed=True,
                     changed=False,
                     results='Unknown state passed. %s' % state,
                     state="unknown")

# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import, locally-disabled
# import module snippets.  This are required
from ansible.module_utils.basic import *
main()
