# pylint: skip-file

def main():
    '''
    ansible oc module for secrets
    '''

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', type='str',
                       choices=['present', 'absent']),
            debug=dict(default=False, type='bool'),
            namespace=dict(default='default', type='str'),
            name=dict(default='router', type='str'),

            kubeconfig=dict(default='/etc/origin/master/admin.kubeconfig', type='str'),
            credentials=dict(default='/etc/origin/master/openshift-router.kubeconfig', type='str'),
            cert_file=dict(default=None, type='str'),
            key_file=dict(default=None, type='str'),
            image=dict(default=None, type='str'), #'openshift3/ose-${component}:${version}'
            latest_image=dict(default=False, type='bool'),
            labels=dict(default=None, type='list'),
            ports=dict(default=['80:80', '443:443'], type='list'),
            replicas=dict(default=1, type='int'),
            selector=dict(default=None, type='str'),
            service_account=dict(default='router', type='str'),
            router_type=dict(default='haproxy-router', type='str'),
            host_network=dict(default=True, type='bool'),
            # external host options
            external_host=dict(default=None, type='str'),
            external_host_vserver=dict(default=None, type='str'),
            external_host_insecure=dict(default=False, type='bool'),
            external_host_partition_path=dict(default=None, type='str'),
            external_host_username=dict(default=None, type='str'),
            external_host_password=dict(default=None, type='str'),
            external_host_private_key=dict(default=None, type='str'),
            # Metrics
            expose_metrics=dict(default=False, type='bool'),
            metrics_image=dict(default=None, type='str'),
            # Stats
            stats_user=dict(default=None, type='str'),
            stats_password=dict(default=None, type='str'),
            stats_port=dict(default=1936, type='int'),

        ),
        mutually_exclusive=[["router_type", "images"]],

        supports_check_mode=True,
    )

    rconfig = RouterConfig(module.params['name'],
                           module.params['kubeconfig'],
                           {'credentials': {'value': module.params['credentials'], 'include': True},
                            'default_cert': {'value': None, 'include': True},
                            'cert_file': {'value': module.params['cert_file'], 'include': False},
                            'key_file': {'value': module.params['key_file'], 'include': False},
                            'image': {'value': module.params['image'], 'include': True},
                            'latest_image': {'value': module.params['latest_image'], 'include': True},
                            'labels': {'value': module.params['labels'], 'include': True},
                            'ports': {'value': ','.join(module.params['ports']), 'include': True},
                            'replicas': {'value': module.params['replicas'], 'include': True},
                            'selector': {'value': module.params['selector'], 'include': True},
                            'service_account': {'value': module.params['service_account'], 'include': True},
                            'router_type': {'value': module.params['router_type'], 'include': False},
                            'host_network': {'value': module.params['host_network'], 'include': True},
                            'external_host': {'value': module.params['external_host'], 'include': True},
                            'external_host_vserver': {'value': module.params['external_host_vserver'],
                                                      'include': True},
                            'external_host_insecure': {'value': module.params['external_host_insecure'],
                                                       'include': True},
                            'external_host_partition_path': {'value': module.params['external_host_partition_path'],
                                                             'include': True},
                            'external_host_username': {'value': module.params['external_host_username'],
                                                       'include': True},
                            'external_host_password': {'value': module.params['external_host_password'],
                                                       'include': True},
                            'external_host_private_key': {'value': module.params['external_host_private_key'],
                                                          'include': True},
                            'expose_metrics': {'value': module.params['expose_metrics'], 'include': True},
                            'metrics_image': {'value': module.params['metrics_image'], 'include': True},
                            'stats_user': {'value': module.params['stats_user'], 'include': True},
                            'stats_password': {'value': module.params['stats_password'], 'include': True},
                            'stats_port': {'value': module.params['stats_port'], 'include': True},
                           })


    ocrouter = Router(rconfig)

    state = module.params['state']

    ########
    # Delete
    ########
    if state == 'absent':
        if not ocrouter.exists():
            module.exit_json(changed=False, state="absent")

        if module.check_mode:
            module.exit_json(change=False, msg='Would have performed a delete.')

        api_rval = ocrouter.delete()
        module.exit_json(changed=True, results=api_rval, state="absent")


    if state == 'present':
        ########
        # Create
        ########
        if not ocrouter.exists():

            if module.check_mode:
                module.exit_json(change=False, msg='Would have performed a create.')

            api_rval = ocrouter.create()

            module.exit_json(changed=True, results=api_rval, state="present")

        ########
        # Update
        ########
        if not ocrouter.needs_update():
            module.exit_json(changed=False, state="present")

        if module.check_mode:
            module.exit_json(change=False, msg='Would have performed an update.')

        api_rval = ocrouter.update()

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
