# pylint: skip-file
# flake8: noqa

def main():
    '''
    ansible oc module for storageclass
    '''

    module = AnsibleModule(
        argument_spec=dict(
            kubeconfig=dict(default='/etc/origin/master/admin.kubeconfig', type='str'),
            state=dict(default='present', type='str', choices=['present', 'absent', 'list']),
            debug=dict(default=False, type='bool'),
            name=dict(default=None, type='str'),
            annotations=dict(default=None, type='dict'),
            parameters=dict(default=None, type='dict'),
            provisioner=dict(required=True, type='str', choices=['aws-ebs', 'gce-pd', 'glusterfs', 'cinder']),
            api_version=dict(default='v1', type='str'),
            default_storage_class=dict(default="false", type='str'),
        ),
        supports_check_mode=True,
    )

    rval = OCStorageClass.run_ansible(module.params, module.check_mode)
    if 'failed' in rval:
        return module.fail_json(**rval)

    return module.exit_json(**rval)


if __name__ == '__main__':
    main()
