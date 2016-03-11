#!/usr/bin/env python
'''
module for openshift cloud secrets
'''
#   Examples:
#
#  # to initiate and use /etc/origin/master/admin.kubeconfig file for auth
#  - name: list secrets
#    oc_secrets:
#      state: list
#      namespace: default
#
#  # To get a specific secret named 'mysecret'
#  - name: list secrets
#    oc_secrets:
#      state: list
#      namespace: default
#      name: mysecret
#
#   # To create a secret:
#   # This module expects the user to place the files on the remote server and pass them in.
#  - name: create a secret from file
#    oc_secrets:
#      state: present
#      namespace: default
#      name: mysecret
#      files:
#      - /tmp/config.yml
#      - /tmp/passwords.yml
#      delete_after: False

#   # To create a secret:
#   # This module expects the user to place the files on the remote server and pass them in.
#  - name: create a secret from content
#    oc_secrets:
#      state: present
#      namespace: default
#      name: mysecret
#      contents:
#      - path: /tmp/config.yml
#        content: "value=True\n"
#      - path: /tmp/passwords.yml
#        content: "test1\ntest2\ntest3\ntest4\n"
#

import os
import shutil
import json
import atexit

class OpenShiftOC(object):
    ''' Class to wrap the oc command line tools
    '''
    def __init__(self,
                 namespace,
                 secret_name=None,
                 kubeconfig='/etc/origin/master/admin.kubeconfig',
                 verbose=False):
        ''' Constructor for OpenshiftOC '''
        self.namespace = namespace
        self.name = secret_name
        self.verbose = verbose
        self.kubeconfig = kubeconfig

    def get_secrets(self):
        '''return a secret by name '''
        cmd = ['get', 'secrets', '-o', 'json', '-n', self.namespace]
        if self.name:
            cmd.append(self.name)

        rval = self.oc_cmd(cmd, output=True)

        # Ensure results are retuned in an array
        if rval.has_key('items'):
            rval['results'] = rval['items']
        elif not isinstance(rval['results'], list):
            rval['results'] = [rval['results']]

        return rval

    def delete_secret(self):
        '''return all pods '''
        return self.oc_cmd(['delete', 'secrets', self.name, '-n', self.namespace])

    def secret_new(self, files):
        '''Create a secret with  all pods '''
        secrets = ["%s=%s" % (os.path.basename(sfile), sfile) for sfile in files]
        cmd = ['-n%s' % self.namespace, 'secrets', 'new', self.name]
        cmd.extend(secrets)

        return self.oc_cmd(cmd)

    @staticmethod
    def create_files_from_contents(data):
        '''Turn an array of dict: filename, content into a files array'''
        files = []
        for sfile in data:
            with open(sfile['path'], 'w') as fds:
                fds.write(sfile['content'])
            files.append(sfile['path'])

        # Register cleanup when module is done
        atexit.register(OpenShiftOC.cleanup, files)
        return files

    def update_secret(self, files, force=False):
        '''run update secret

           This receives a list of file names and converts it into a secret.
           The secret is then written to disk and passed into the `oc replace` command.
        '''
        secret = self.prep_secret(files)
        if secret['returncode'] != 0:
            return secret

        sfile_path = '/tmp/%s' % secret['results']['metadata']['name']
        with open(sfile_path, 'w') as sfd:
            sfd.write(json.dumps(secret['results']))

        cmd = ['replace', '-f', sfile_path]
        if force:
            cmd = ['replace', '--force', '-f', sfile_path]

        atexit.register(OpenShiftOC.cleanup, [sfile_path])

        return self.oc_cmd(cmd)

    def prep_secret(self, files):
        ''' return what the secret would look like if created
            This is accomplished by passing -ojson.  This will most likely change in the future
        '''
        secrets = ["%s=%s" % (os.path.basename(sfile), sfile) for sfile in files]
        cmd = ['-ojson', '-n%s' % self.namespace, 'secrets', 'new', self.name]
        cmd.extend(secrets)

        return self.oc_cmd(cmd, output=True)

    def oc_cmd(self, cmd, output=False):
        '''Base command for oc '''
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

    @staticmethod
    def cleanup(files):
        '''Clean up on exit '''
        for sfile in files:
            if os.path.exists(sfile):
                if os.path.isdir(sfile):
                    shutil.rmtree(sfile)
                elif os.path.isfile(sfile):
                    os.remove(sfile)


def exists(results, _name):
    ''' Check to see if the results include the name '''
    if not results:
        return False

    if find_result(results, _name):
        return True

    return False

def find_result(results, _name):
    ''' Find the specified result by name'''
    rval = None
    for result in results:
        #print "%s == %s" % (result['metadata']['name'], name)
        if result.has_key('metadata') and result['metadata']['name'] == _name:
            rval = result
            break

    return rval

# Disabling too-many-branches.  This is a yaml dictionary comparison function
# pylint: disable=too-many-branches,too-many-return-statements
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

            result = check_def_equal(user_def[key], value)
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
    occmd = OpenShiftOC(module.params['namespace'],
                        module.params['name'],
                        kubeconfig=module.params['kubeconfig'],
                        verbose=module.params['debug'])

    state = module.params['state']

    api_rval = occmd.get_secrets()

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
        if not exists(api_rval['results'], module.params['name']):
            module.exit_json(changed=False, state="absent")

        if module.check_mode:
            module.exit_json(change=False, msg='Would have performed a delete.')

        api_rval = occmd.delete_secret()
        module.exit_json(changed=True, results=api_rval, state="absent")


    if state == 'present':
        if module.params['files']:
            files = module.params['files']
        elif module.params['contents']:
            files = OpenShiftOC.create_files_from_contents(module.params['contents'])
        else:
            module.fail_json(msg='Either specify files or contents.')

        ########
        # Create
        ########
        if not exists(api_rval['results'], module.params['name']):

            if module.check_mode:
                module.exit_json(change=False, msg='Would have performed a create.')

            api_rval = occmd.secret_new(files)

            # Remove files
            if files and module.params['delete_after']:
                OpenShiftOC.cleanup(files)

            module.exit_json(changed=True, results=api_rval, state="present")

        ########
        # Update
        ########
        secret = occmd.prep_secret(files)

        if secret['returncode'] != 0:
            module.fail_json(msg=secret)

        if check_def_equal(secret['results'], api_rval['results'][0]):

            # Remove files
            if files and module.params['delete_after']:
                OpenShiftOC.cleanup(files)

            module.exit_json(changed=False, results=secret['results'], state="present")

        if module.check_mode:
            module.exit_json(change=False, msg='Would have performed an update.')

        api_rval = occmd.update_secret(files, force=module.params['force'])

        # Remove files
        if files and module.params['delete_after']:
            OpenShiftOC.cleanup(files)

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
