#!usr/bin/env python
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
import yaml

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
        for key, value in content.items():
            yed.put(key, value)

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

        results = ''

        if self.verbose:
            print ' '.join(cmds)

        proc = subprocess.Popen(cmds,
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                env={'KUBECONFIG': self.kubeconfig})
        proc.wait()
        if proc.returncode == 0:
            if output:
                try:
                    results = json.loads(proc.stdout.read())
                except ValueError as err:
                    if "No JSON object could be decoded" in err.message:
                        results = err.message

            if self.verbose:
                print proc.stderr.read()
                print results
                print

            return {"returncode": proc.returncode, "results": results}

        return {"returncode": proc.returncode,
                "stderr": proc.stderr.read(),
                "stdout": proc.stdout.read(),
                "results": {}
               }

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
            contents = yaml.load(contents)
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

    def __init__(self, filename=None, content=None):
        self.content = content
        self.filename = filename
        self.__yaml_dict = content
        if self.filename and not self.content:
            self.get()
        elif self.filename and self.content:
            self.write()

    @property
    def yaml_dict(self):
        ''' getter method for yaml_dict '''
        return self.__yaml_dict

    @yaml_dict.setter
    def yaml_dict(self, value):
        ''' setter method for yaml_dict '''
        self.__yaml_dict = value

    @staticmethod
    def remove_entry(data, keys):
        ''' remove an item from a dictionary with key notation a.b.c
            d = {'a': {'b': 'c'}}}
            keys = a.b
            item = c
        '''
        if "." in keys:
            key, rest = keys.split(".", 1)
            if key in data.keys():
                Yedit.remove_entry(data[key], rest)
        else:
            del data[keys]

    @staticmethod
    def add_entry(data, keys, item):
        ''' Add an item to a dictionary with key notation a.b.c
            d = {'a': {'b': 'c'}}}
            keys = a.b
            item = c
        '''
        if "." in keys:
            key, rest = keys.split(".", 1)
            if key not in data:
                data[key] = {}

            if not isinstance(data, dict):
                raise YeditException('Invalid add_entry called on a [%s] of type [%s].' % (data, type(data)))
            else:
                Yedit.add_entry(data[key], rest, item)

        else:
            data[keys] = item


    @staticmethod
    def get_entry(data, keys):
        ''' Get an item from a dictionary with key notation a.b.c
            d = {'a': {'b': 'c'}}}
            keys = a.b
            return c
        '''
        if keys and "." in keys:
            key, rest = keys.split(".", 1)
            if not isinstance(data[key], dict):
                raise YeditException('Invalid get_entry called on a [%s] of type [%s].' % (data, type(data)))

            else:
                return Yedit.get_entry(data[key], rest)

        else:
            return data.get(keys, None)


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

    def get(self):
        ''' return yaml file '''
        contents = self.read()

        if not contents:
            return None

        # check if it is yaml
        try:
            self.yaml_dict = yaml.load(contents)
        except yaml.YAMLError as _:
            # Error loading yaml
            return None

        return self.yaml_dict

    def delete(self, key):
        ''' put key, value into a yaml file '''
        try:
            entry = Yedit.get_entry(self.yaml_dict, key)
        except KeyError as _:
            entry = None
        if not entry:
            return  (False, self.yaml_dict)

        Yedit.remove_entry(self.yaml_dict, key)
        self.write()
        return (True, self.get())

    def put(self, key, value):
        ''' put key, value into a yaml file '''
        try:
            entry = Yedit.get_entry(self.yaml_dict, key)
        except KeyError as _:
            entry = None

        if entry == value:
            return (False, self.yaml_dict)

        Yedit.add_entry(self.yaml_dict, key, value)
        self.write()
        return (True, self.get())

    def create(self, key, value):
        ''' create the file '''
        if not self.exists():
            self.yaml_dict = {key: value}
            self.write()
            return (True, self.get())

        return (False, self.get())

class OCObject(OpenShiftCLI):
    ''' Class to wrap the oc command line tools '''

    # pylint allows 5. we need 6
    # pylint: disable=too-many-arguments
    def __init__(self,
                 kind,
                 namespace,
                 rname=None,
                 kubeconfig='/etc/origin/master/admin.kubeconfig',
                 verbose=False):
        ''' Constructor for OpenshiftOC '''
        super(OCObject, self).__init__(namespace, kubeconfig)
        self.kind = kind
        self.namespace = namespace
        self.name = rname
        self.kubeconfig = kubeconfig
        self.verbose = verbose

    def get(self):
        '''return a deploymentconfig by name '''
        return self._get(self.kind, rname=self.name)

    def delete(self):
        '''return all pods '''
        return self._delete(self.kind, self.name)

    def create(self, files=None, content=None):
        '''Create a deploymentconfig '''
        if files:
            return self._create(files[0])

        return self._create(Utils.create_files_from_contents(content))


    # pylint: disable=too-many-function-args
    def update(self, files=None, content=None, force=False):
        '''run update dc

           This receives a list of file names and takes the first filename and calls replace.
        '''
        if files:
            return self._replace(files[0], force)

        return self.update_content(content, force)

    def update_content(self, content, force=False):
        '''update the dc with the content'''
        return self._replace_content(self.kind, self.name, content, force=force)

    def needs_update(self, files=None, content=None, content_type='yaml'):
        ''' check to see if we need to update '''
        objects = self.get()
        if objects['returncode'] != 0:
            return objects

        # pylint: disable=no-member
        data = None
        if files:
            data = Utils.get_resource_file(files[0], content_type)

            # if equal then no need.  So not equal is True
            return not Utils.check_def_equal(data, objects['results'][0], True)
        else:
            data = content

            for key, value in data.items():
                if key == 'metadata':
                    continue
                if not objects['results'][0].has_key(key):
                    return True
                if value != objects['results'][0][key]:
                    return True

        return False


# pylint: disable=too-many-branches
def main():
    '''
    ansible oc module for services
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
            kind=dict(required=True,
                      type='str',
                      choices=['dc', 'deploymentconfig',
                               'svc', 'service',
                               'secret',
                              ]),
            delete_after=dict(default=False, type='bool'),
            content=dict(default=None, type='dict'),
            force=dict(default=False, type='bool'),
        ),
        mutually_exclusive=[["content", "files"]],

        supports_check_mode=True,
    )
    ocobj = OCObject(module.params['kind'],
                     module.params['namespace'],
                     module.params['name'],
                     kubeconfig=module.params['kubeconfig'],
                     verbose=module.params['debug'])

    state = module.params['state']

    api_rval = ocobj.get()

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

        api_rval = ocobj.delete()
        module.exit_json(changed=True, results=api_rval, state="absent")

    if state == 'present':
        ########
        # Create
        ########
        if not Utils.exists(api_rval['results'], module.params['name']):

            if module.check_mode:
                module.exit_json(change=False, msg='Would have performed a create.')

            # Create it here
            api_rval = ocobj.create(module.params['files'], module.params['content'])
            if api_rval['returncode'] != 0:
                module.fail_json(msg=api_rval)

            # return the created object
            api_rval = ocobj.get()

            if api_rval['returncode'] != 0:
                module.fail_json(msg=api_rval)

            # Remove files
            if module.params['files'] and module.params['delete_after']:
                Utils.cleanup(module.params['files'])

            module.exit_json(changed=True, results=api_rval, state="present")

        ########
        # Update
        ########
        # if a file path is passed, use it.
        update = ocobj.needs_update(module.params['files'], module.params['content'])
        if not isinstance(update, bool):
            module.fail_json(msg=update)

        # No changes
        if not update:
            if module.params['files'] and module.params['delete_after']:
                Utils.cleanup(module.params['files'])

            module.exit_json(changed=False, results=api_rval['results'][0], state="present")

        if module.check_mode:
            module.exit_json(change=False, msg='Would have performed an update.')

        api_rval = ocobj.update(module.params['files'],
                                module.params['content'],
                                module.params['force'])


        if api_rval['returncode'] != 0:
            module.fail_json(msg=api_rval)

        # return the created object
        api_rval = ocobj.get()

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
