# pylint: skip-file

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
