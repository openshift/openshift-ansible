# pylint: skip-file
# flake8: noqa

def main():
    '''
    ansible oc module for validating OpenShift SDN objects
    '''

    module = AnsibleModule(
        argument_spec=dict(
            kubeconfig=dict(default='/etc/origin/master/admin.kubeconfig', type='str'),
        ),
        supports_check_mode=False,
    )


    rval = OCSDNValidator.run_ansible(module.params)
    if 'failed' in rval:
        module.fail_json(**rval)

    module.exit_json(**rval)

if __name__ == '__main__':
    main()
