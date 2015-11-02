#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4

"""Ansible module for modifying OpenShift configs during an upgrade"""

DOCUMENTATION = '''
---
module: openshift_upgrade_config
short_description: OpenShift Upgrade Config
author: Jason DeTiberus
requirements: [ ]
'''
EXAMPLES = '''
'''

def upgrade_master_3_0_to_3_1(backup):
    pass


def upgrade_master(from_version, to_version, backup):
    if from_version == '3.0':
        if to_version == '3.1':
            upgrade_master_3_0_to_3_1(backup)


def main():
    """ main """
    # disabling pylint errors for global-variable-undefined and invalid-name
    # for 'global module' usage, since it is required to use ansible_facts
    # pylint: disable=global-variable-undefined, invalid-name
    global module

    module = AnsibleModule(
        argument_spec=dict(
            from_version=dict(required=True, choices=['3.0']),
            to_version=dict(required=True, choices=['3.1']),
            role=dict(required=True, choices=['master']),
            backup=dict(required=False, default=True, type='bool')
        ),
        supports_check_mode=True,
    )

    changed = False

    from_version = module.params['from_version']
    to_version = module.params['to_version']
    role = module.params['role']
    backup = module.params['backup']

    if role == 'master':
        upgrade_master(from_version, to_version, backup)

    return module.exit_json(changed=changed)

# ignore pylint errors related to the module_utils import
# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import
# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
