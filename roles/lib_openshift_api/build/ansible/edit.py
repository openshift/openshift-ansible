# pylint: skip-file

def main():
    '''
    ansible oc module for services
    '''

    module = AnsibleModule(
        argument_spec=dict(
            kubeconfig=dict(default='/etc/origin/master/admin.kubeconfig', type='str'),
            state=dict(default='present', type='str',
                       choices=['present']),
            debug=dict(default=False, type='bool'),
            namespace=dict(default='default', type='str'),
            name=dict(default=None, required=True, type='str'),
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
            file_name=dict(default=None, type='str'),
            file_format=dict(default='yaml', type='str'),
            content=dict(default=None, required=True, type='dict'),
            force=dict(default=False, type='bool'),
        ),
        supports_check_mode=True,
    )
    ocedit = Edit(module.params['kind'],
                  module.params['namespace'],
                  module.params['name'],
                  kubeconfig=module.params['kubeconfig'],
                  verbose=module.params['debug'])

    state = module.params['state']

    api_rval = ocedit.get()

    ########
    # Create
    ########
    if not Utils.exists(api_rval['results'], module.params['name']):
        module.fail_json(msg=api_rval)

    ########
    # Update
    ########
    api_rval = ocedit.update(module.params['file_name'],
                             module.params['content'],
                             module.params['force'],
                             module.params['file_format'])


    if api_rval['returncode'] != 0:
        module.fail_json(msg=api_rval)

    if api_rval.has_key('updated') and not api_rval['updated']:
        module.exit_json(changed=False, results=api_rval, state="present")

    # return the created object
    api_rval = ocedit.get()

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
