# pylint: skip-file
# flake8: noqa

def main():
    '''
    ansible oc adm module for ca create-server-cert
    '''

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', type='str', choices=['present']),
            debug=dict(default=False, type='bool'),
            kubeconfig=dict(default='/etc/origin/master/admin.kubeconfig', type='str'),
            cmd=dict(default=None, require=True, type='str'),
            # oadm ca create-server-cert [options]
            cert=dict(default=None, type='str'),
            key=dict(default=None, type='str'),
            signer_cert=dict(default=None, type='str'),
            signer_key=dict(default=None, type='str'),
            signer_serial=dict(default=None, type='str'),
            hostnames=dict(default=[], type='list'),
            overwrite=dict(default=False, type='bool'),
        ),
        supports_check_mode=True,
    )

    # pylint: disable=line-too-long
    results = CAServerCert.run_ansible(module.params, module.check_mode)
    if 'failed' in results:
        return module.fail_json(**results)

    return module.exit_json(**results)


if __name__ == '__main__':
    main()
