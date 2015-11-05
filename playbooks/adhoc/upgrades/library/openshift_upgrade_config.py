#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4

"""Ansible module for modifying OpenShift configs during an upgrade"""

import os
import yaml

DOCUMENTATION = '''
---
module: openshift_upgrade_config
short_description: OpenShift Upgrade Config
author: Jason DeTiberus
requirements: [ ]
'''
EXAMPLES = '''
'''


def upgrade_master_3_0_to_3_1(module, config_base, backup):
    """Main upgrade method for 3.0 to 3.1."""
    changes = []

    # Facts do not get transferred to the hosts where custom modules run,
    # need to make some assumptions here.
    master_config = os.path.join(config_base, 'master/master-config.yaml')

    master_cfg_file = open(master_config, 'r')
    config = yaml.safe_load(master_cfg_file.read())
    master_cfg_file.close()

    # Remove v1beta3 from apiLevels:
    if 'apiLevels' in config and \
        'v1beta3' in config['apiLevels']:
        config['apiLevels'].remove('v1beta3')
        changed = True
        changes.append("master-config.yaml: removed v1beta3 from apiLevels")
    if 'apiLevels' in config['kubernetesMasterConfig'] and \
        'v1beta3' in config['kubernetesMasterConfig']['apiLevels']:
        config['kubernetesMasterConfig']['apiLevels'].remove('v1beta3')
        changed = True

    # Add the new master proxy client certs:
    # TODO: re-enable this once these certs are generated during upgrade:
#    if 'proxyClientInfo' not in config['kubernetesMasterConfig']:
#        config['kubernetesMasterConfig']['proxyClientInfo'] = {
#            'certFile': 'master.proxy-client.crt',
#            'keyFile': 'master.proxy-client.key'
#       }
#        changes.append("master-config.yaml: added proxyClientInfo")

    if len(changes) > 0:
        if backup:
            # TODO: Check success:
            module.backup_local(master_config)

        # Write the modified config:
        out_file = open(master_config, 'w')
        out_file.write(yaml.safe_dump(config, default_flow_style=False))
        out_file.close()

    return changes


def upgrade_master(module, config_base, from_version, to_version, backup):
    """Upgrade entry point."""
    if from_version == '3.0':
        if to_version == '3.1':
            return upgrade_master_3_0_to_3_1(module, config_base, backup)


def main():
    """ main """
    # disabling pylint errors for global-variable-undefined and invalid-name
    # for 'global module' usage, since it is required to use ansible_facts
    # pylint: disable=global-variable-undefined, invalid-name
    global module

    module = AnsibleModule(
        argument_spec=dict(
            config_base=dict(required=True),
            from_version=dict(required=True, choices=['3.0']),
            to_version=dict(required=True, choices=['3.1']),
            role=dict(required=True, choices=['master']),
            backup=dict(required=False, default=True, type='bool')
        ),
        supports_check_mode=True,
    )

    from_version = module.params['from_version']
    to_version = module.params['to_version']
    role = module.params['role']
    backup = module.params['backup']
    config_base = module.params['config_base']

    try:
        changes = []
        if role == 'master':
            changes = upgrade_master(module, config_base, from_version,
                to_version, backup)

        changed = len(changes) > 0
        return module.exit_json(changed=changed, changes=changes)
    except Exception, e:
        return module.fail_json(msg=str(e))

# ignore pylint errors related to the module_utils import
# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import
# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
