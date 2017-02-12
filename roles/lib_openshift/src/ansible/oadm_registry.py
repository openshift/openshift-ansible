# pylint: skip-file
# flake8: noqa

def main():
    '''
    ansible oc module for registry
    '''

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', type='str',
                       choices=['present', 'absent']),
            debug=dict(default=False, type='bool'),
            namespace=dict(default='default', type='str'),
            name=dict(default=None, required=True, type='str'),

            kubeconfig=dict(default='/etc/origin/master/admin.kubeconfig', type='str'),
            credentials=dict(default='/etc/origin/master/openshift-registry.kubeconfig', type='str'),
            images=dict(default=None, type='str'),
            latest_images=dict(default=False, type='bool'),
            labels=dict(default=None, type='list'),
            ports=dict(default=['5000'], type='list'),
            replicas=dict(default=1, type='int'),
            selector=dict(default=None, type='str'),
            service_account=dict(default='registry', type='str'),
            mount_host=dict(default=None, type='str'),
            registry_type=dict(default='docker-registry', type='str'),
            template=dict(default=None, type='str'),
            volume=dict(default='/registry', type='str'),
            env_vars=dict(default=None, type='dict'),
            volume_mounts=dict(default=None, type='list'),
            edits=dict(default=None, type='list'),
            force=dict(default=False, type='bool'),
        ),
        mutually_exclusive=[["registry_type", "images"]],

        supports_check_mode=True,
    )

    results = Registry.run_ansible(module.params, module.check_mode)
    if 'failed' in results:
        module.fail_json(**results)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
