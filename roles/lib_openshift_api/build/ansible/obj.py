# pylint: skip-file

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
                               'scc', 'securitycontextconstraints',
                               'ns', 'namespace', 'project', 'projects',
                               'is', 'imagestream',
                               'istag', 'imagestreamtag',
                               'bc', 'buildconfig',
                               'routes',
                               'node',
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
