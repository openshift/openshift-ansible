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
    ''' Class to wrap the oc command line tools '''
    def __init__(self,
                 namespace,
                 kubeconfig='/etc/origin/master/admin.kubeconfig',
                 verbose=False):
        ''' Constructor for OpenshiftOC '''
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
        return self.oc_cmd(cmd)

    def _create(self, fname):
        '''return all pods '''
        return self.oc_cmd(['create', '-f', fname, '-n', self.namespace])

    def _delete(self, resource, rname):
        '''return all pods '''
        return self.oc_cmd(['delete', resource, rname, '-n', self.namespace])

    def _get(self, resource, rname=None):
        '''return a secret by name '''
        cmd = ['get', resource, '-o', 'json', '-n', self.namespace]
        if rname:
            cmd.append(rname)

        rval = self.oc_cmd(cmd, output=True)

        # Ensure results are retuned in an array
        if rval.has_key('items'):
            rval['results'] = rval['items']
        elif not isinstance(rval['results'], list):
            rval['results'] = [rval['results']]

        return rval

    def oc_cmd(self, cmd, output=False):
        '''Base command for oc '''
        #cmds = ['/usr/bin/oc', '--config', self.kubeconfig]
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
               }

        if proc.returncode == 0:
            if output:
                try:
                    rval['results'] = json.loads(stdout)
                except ValueError as err:
                    if "No JSON object could be decoded" in err.message:
                        err = err.message

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
    def check_def_equal(user_def, result_def, debug=False):
        ''' Given a user defined definition, compare it with the results given back by our query.  '''

        # Currently these values are autogenerated and we do not need to check them
        skip = ['metadata', 'status']

        for key, value in result_def.items():
            if key in skip:
                continue

            # Both are lists
            if isinstance(value, list):
                if not isinstance(user_def[key], list):
                    return False

                # lists should be identical
                if value != user_def[key]:
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

                result = Utils.check_def_equal(user_def[key], value, debug=debug)
                if not result:
                    if debug:
                        print "dict returned false"
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

class Secret(OpenShiftCLI):
    ''' Class to wrap the oc command line tools
    '''
    def __init__(self,
                 namespace,
                 secret_name=None,
                 kubeconfig='/etc/origin/master/admin.kubeconfig',
                 verbose=False):
        ''' Constructor for OpenshiftOC '''
        super(Secret, self).__init__(namespace, kubeconfig)
        self.namespace = namespace
        self.name = secret_name
        self.kubeconfig = kubeconfig
        self.verbose = verbose

    def get(self):
        '''return a secret by name '''
        return self._get('secrets', self.name)

    def delete(self):
        '''delete a secret by name'''
        return self._delete('secrets', self.name)

    def create(self, files=None, contents=None):
        '''Create a secret '''
        if not files:
            files = Utils.create_files_from_contents(contents)

        secrets = ["%s=%s" % (os.path.basename(sfile), sfile) for sfile in files]
        cmd = ['-n%s' % self.namespace, 'secrets', 'new', self.name]
        cmd.extend(secrets)

        return self.oc_cmd(cmd)

    def update(self, files, force=False):
        '''run update secret

           This receives a list of file names and converts it into a secret.
           The secret is then written to disk and passed into the `oc replace` command.
        '''
        secret = self.prep_secret(files)
        if secret['returncode'] != 0:
            return secret

        sfile_path = '/tmp/%s' % self.name
        with open(sfile_path, 'w') as sfd:
            sfd.write(json.dumps(secret['results']))

        atexit.register(Utils.cleanup, [sfile_path])

        return self._replace(sfile_path, force=force)

    def prep_secret(self, files=None, contents=None):
        ''' return what the secret would look like if created
            This is accomplished by passing -ojson.  This will most likely change in the future
        '''
        if not files:
            files = Utils.create_files_from_contents(contents)

        secrets = ["%s=%s" % (os.path.basename(sfile), sfile) for sfile in files]
        cmd = ['-ojson', '-n%s' % self.namespace, 'secrets', 'new', self.name]
        cmd.extend(secrets)

        return self.oc_cmd(cmd, output=True)



# pylint: disable=too-many-branches
def main():
    '''
    ansible oc module for secrets
    '''

    module = AnsibleModule(
        argument_spec=dict(
            kubeconfig=dict(default='/etc/origin/master/admin.kubeconfig', type='str'),
            state=dict(default='present', type='str',
                       choices=['present', 'absent', 'list']),
            debug=dict(default=False, type='bool'),
            namespace=dict(default='default', type='str'),
            name=dict(default=None, type='str'),
            files=dict(default=None, type='list'),
            delete_after=dict(default=False, type='bool'),
            contents=dict(default=None, type='list'),
            force=dict(default=False, type='bool'),
        ),
        mutually_exclusive=[["contents", "files"]],

        supports_check_mode=True,
    )
    occmd = Secret(module.params['namespace'],
                   module.params['name'],
                   kubeconfig=module.params['kubeconfig'],
                   verbose=module.params['debug'])

    state = module.params['state']

    api_rval = occmd.get()

    #####
    # Get
    #####
    if state == 'list':
        module.exit_json(changed=False, results=api_rval['results'], state="list")

    if not module.params['name']:
        module.fail_json(msg='Please specify a name when state is absent|present.')
    ########
    # Delete
    ########
    if state == 'absent':
        if not Utils.exists(api_rval['results'], module.params['name']):
            module.exit_json(changed=False, state="absent")

        if module.check_mode:
            module.exit_json(change=False, msg='Would have performed a delete.')

        api_rval = occmd.delete()
        module.exit_json(changed=True, results=api_rval, state="absent")


    if state == 'present':
        if module.params['files']:
            files = module.params['files']
        elif module.params['contents']:
            files = Utils.create_files_from_contents(module.params['contents'])
        else:
            module.fail_json(msg='Either specify files or contents.')

        ########
        # Create
        ########
        if not Utils.exists(api_rval['results'], module.params['name']):

            if module.check_mode:
                module.exit_json(change=False, msg='Would have performed a create.')

            api_rval = occmd.create(module.params['files'], module.params['contents'])

            # Remove files
            if files and module.params['delete_after']:
                Utils.cleanup(files)

            module.exit_json(changed=True, results=api_rval, state="present")

        ########
        # Update
        ########
        secret = occmd.prep_secret(module.params['files'], module.params['contents'])

        if secret['returncode'] != 0:
            module.fail_json(msg=secret)

        if Utils.check_def_equal(secret['results'], api_rval['results'][0]):

            # Remove files
            if files and module.params['delete_after']:
                Utils.cleanup(files)

            module.exit_json(changed=False, results=secret['results'], state="present")

        if module.check_mode:
            module.exit_json(change=False, msg='Would have performed an update.')

        api_rval = occmd.update(files, force=module.params['force'])

        # Remove files
        if secret and module.params['delete_after']:
            Utils.cleanup(files)

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
