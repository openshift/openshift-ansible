#!/usr/bin/env python
'''
  OpenShiftCLI class that wraps the oc commands in a subprocess
'''
import atexit
import json
import os
import shutil
import subprocess
import yaml

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

    def replace(self, fname, force=False):
        '''return all pods '''
        cmd = ['replace', '-f', fname]
        if force:
            cmd = ['replace', '--force', '-f', fname]
        return self.oc_cmd(cmd)

    def create(self, fname):
        '''return all pods '''
        return self.oc_cmd(['create', '-f', fname, '-n', self.namespace])

    def delete(self, resource, rname):
        '''return all pods '''
        return self.oc_cmd(['delete', resource, rname, '-n', self.namespace])

    def get(self, resource, rname=None):
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
                fds.write(yaml.dump(data, default_flow_style=False))

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
        skip = ['creationTimestamp', 'selfLink', 'resourceVersion', 'uid', 'namespace']

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

class DeploymentConfig(OpenShiftCLI):
    ''' Class to wrap the oc command line tools
    '''
    def __init__(self,
                 namespace,
                 dname=None,
                 kubeconfig='/etc/origin/master/admin.kubeconfig',
                 verbose=False):
        ''' Constructor for OpenshiftOC '''
        super(DeploymentConfig, self).__init__(namespace, kubeconfig)
        self.namespace = namespace
        self.name = dname
        self.kubeconfig = kubeconfig
        self.verbose = verbose

    def get_dc(self):
        '''return a deploymentconfig by name '''
        return self.get('dc', self.name)

    def delete_dc(self):
        '''return all pods '''
        return self.delete('dc', self.name)

    def new_dc(self, dfile):
        '''Create a deploymentconfig '''
        return self.create(dfile)

    def update_dc(self, dfile, force=False):
        '''run update dc

           This receives a list of file names and takes the first filename and calls replace.
        '''
        return self.replace(dfile, force)


# pylint: disable=too-many-branches
def main():
    '''
    ansible oc module for deploymentconfig
    '''

    module = AnsibleModule(
        argument_spec=dict(
            kubeconfig=dict(default='/etc/origin/master/admin.kubeconfig', type='str'),
            state=dict(default='present', type='str',
                       choices=['present', 'absent', 'list']),
            debug=dict(default=False, type='bool'),
            namespace=dict(default='default', type='str'),
            name=dict(default=None, type='str'),
            deploymentconfig_file=dict(default=None, type='str'),
            input_type=dict(default='yaml', choices=['yaml', 'json'], type='str'),
            delete_after=dict(default=False, type='bool'),
            content=dict(default=None, type='dict'),
            force=dict(default=False, type='bool'),
        ),
        mutually_exclusive=[["contents", "deploymentconfig_file"]],

        supports_check_mode=True,
    )
    occmd = DeploymentConfig(module.params['namespace'],
                             dname=module.params['name'],
                             kubeconfig=module.params['kubeconfig'],
                             verbose=module.params['debug'])

    state = module.params['state']

    api_rval = occmd.get_dc()

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

        api_rval = occmd.delete_dc()
        module.exit_json(changed=True, results=api_rval, state="absent")


    if state == 'present':
        if module.params['deploymentconfig_file']:
            dfile = module.params['deploymentconfig_file']
        elif module.params['content']:
            dfile = Utils.create_file('dc', module.params['content'])
        else:
            module.fail_json(msg="Please specify content or deploymentconfig file.")

        ########
        # Create
        ########
        if not Utils.exists(api_rval['results'], module.params['name']):

            if module.check_mode:
                module.exit_json(change=False, msg='Would have performed a create.')

            api_rval = occmd.new_dc(dfile)

            # Remove files
            if module.params['deploymentconfig_file'] and module.params['delete_after']:
                Utils.cleanup([dfile])

            if api_rval['returncode'] != 0:
                module.fail_json(msg=api_rval)

            module.exit_json(changed=True, results=api_rval, state="present")

        ########
        # Update
        ########
        if Utils.check_def_equal(Utils.get_resource_file(dfile), api_rval['results'][0]):

            # Remove files
            if module.params['deploymentconfig_file'] and module.params['delete_after']:
                Utils.cleanup([dfile])

            module.exit_json(changed=False, results=api_rval['results'], state="present")

        if module.check_mode:
            module.exit_json(change=False, msg='Would have performed an update.')

        api_rval = occmd.update_dc(dfile, force=module.params['force'])

        # Remove files
        if module.params['deploymentconfig_file'] and module.params['delete_after']:
            Utils.cleanup([dfile])

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
