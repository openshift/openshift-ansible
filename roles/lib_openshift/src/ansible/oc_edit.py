# pylint: skip-file
# flake8: noqa


def main():
    '''
    ansible oc module for editing objects
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
                               'rc', 'replicationcontroller',
                               'svc', 'service',
                               'scc', 'securitycontextconstraints',
                               'ns', 'namespace', 'project', 'projects',
                               'is', 'imagestream',
                               'istag', 'imagestreamtag',
                               'bc', 'buildconfig',
                               'routes',
                               'node',
                               'secret',
                               'pv', 'persistentvolume']),
            file_name=dict(default=None, type='str'),
            file_format=dict(default='yaml', type='str'),
            content=dict(default=None, required=True, type='dict'),
            force=dict(default=False, type='bool'),
            separator=dict(default='.', type='str'),
        ),
        supports_check_mode=True,
    )

    rval = Edit.run_ansible(module.params, module.check_mode)
    if 'failed' in rval:
        module.fail_json(**rval)

    module.exit_json(**rval)

if __name__ == '__main__':
    main()
