# pylint: skip-file
# flake8: noqa


def get_cert_data(path, content):
    '''get the data for a particular value'''
    if not path and not content:
        return None

    rval = None
    if path and os.path.exists(path) and os.access(path, os.R_OK):
        rval = open(path).read()
    elif content:
        rval = content

    return rval


# pylint: disable=too-many-branches
def main():
    '''
    ansible oc module for route
    '''
    module = AnsibleModule(
        argument_spec=dict(
            kubeconfig=dict(default='/etc/origin/master/admin.kubeconfig', type='str'),
            state=dict(default='present', type='str',
                       choices=['present', 'absent', 'list']),
            debug=dict(default=False, type='bool'),
            name=dict(default=None, required=True, type='str'),
            namespace=dict(default=None, required=True, type='str'),
            tls_termination=dict(default=None, type='str'),
            dest_cacert_path=dict(default=None, type='str'),
            cacert_path=dict(default=None, type='str'),
            cert_path=dict(default=None, type='str'),
            key_path=dict(default=None, type='str'),
            dest_cacert_content=dict(default=None, type='str'),
            cacert_content=dict(default=None, type='str'),
            cert_content=dict(default=None, type='str'),
            key_content=dict(default=None, type='str'),
            service_name=dict(default=None, type='str'),
            host=dict(default=None, type='str'),
            wildcard_policy=dict(default=None, type='str'),
            weight=dict(default=None, type='int'),
        ),
        mutually_exclusive=[('dest_cacert_path', 'dest_cacert_content'),
                            ('cacert_path', 'cacert_content'),
                            ('cert_path', 'cert_content'),
                            ('key_path', 'key_content'), ],
        supports_check_mode=True,
    )
    files = {'destcacert': {'path': module.params['dest_cacert_path'],
                            'content': module.params['dest_cacert_content'],
                            'value': None, },
             'cacert': {'path': module.params['cacert_path'],
                        'content': module.params['cacert_content'],
                        'value': None, },
             'cert': {'path': module.params['cert_path'],
                      'content': module.params['cert_content'],
                      'value': None, },
             'key': {'path': module.params['key_path'],
                     'content': module.params['key_content'],
                     'value': None, }, }

    if module.params['tls_termination']:
        for key, option in files.items():
            if key == 'destcacert' and module.params['tls_termination'] != 'reencrypt':
                continue

            option['value'] = get_cert_data(option['path'], option['content'])

            if not option['value']:
                module.fail_json(msg='Verify that you pass a value for %s' % key)

    results = OCRoute.run_ansible(module.params, files, module.check_mode)

    if 'failed' in results:
        module.fail_json(**results)

    module.exit_json(**results)


if __name__ == '__main__':
    main()
