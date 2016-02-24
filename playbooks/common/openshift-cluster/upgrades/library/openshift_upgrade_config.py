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

def modify_api_levels(level_list, remove, ensure, msg_prepend='',
                      msg_append=''):
    """ modify_api_levels """
    changed = False
    changes = []

    if not isinstance(remove, list):
        remove = []

    if not isinstance(ensure, list):
        ensure = []

    if not isinstance(level_list, list):
        new_list = []
        changed = True
        changes.append("%s created missing %s" % (msg_prepend, msg_append))
    else:
        new_list = level_list
        for level in remove:
            if level in new_list:
                new_list.remove(level)
                changed = True
                changes.append("%s removed %s %s" % (msg_prepend, level, msg_append))

    for level in ensure:
        if level not in new_list:
            new_list.append(level)
            changed = True
            changes.append("%s added %s %s" % (msg_prepend, level, msg_append))

    return {'new_list': new_list, 'changed': changed, 'changes': changes}


def read_config(config_file):
    with open(config_file, 'r') as cfg_file:
        config = yaml.safe_load(cfg_file.read())
    return config


def write_config(config, config_file):
    with open(config_file, 'w') as out_file:
        out_file.write(yaml.safe_dump(config, default_flow_style=False))


def upgrade_3_0_to_3_1(role, ansible_module, config_base, backup):
    """Main upgrade method for 3.0 to 3.1."""
    changes = []

    if role == 'master':
        # Facts do not get transferred to the hosts where custom modules run,
        # need to make some assumptions here.
        config_file = os.path.join(config_base, role, '{0}-config.yaml'.format(role))
        config = read_config(config_file)

        # Remove unsupported api versions and ensure supported api versions from
        # master config
        unsupported_levels = ['v1beta1', 'v1beta2', 'v1beta3']
        supported_levels = ['v1']

        result = modify_api_levels(config.get('apiLevels'), unsupported_levels,
                                   supported_levels, 'master-config.yaml:', 'from apiLevels')
        if result['changed']:
            config['apiLevels'] = result['new_list']
            changes.append(result['changes'])

        if 'kubernetesMasterConfig' in config and 'apiLevels' in config['kubernetesMasterConfig']:
            config['kubernetesMasterConfig'].pop('apiLevels')
            changes.append('master-config.yaml: removed kubernetesMasterConfig.apiLevels')

        # Add masterCA to serviceAccountConfig
        if 'serviceAccountConfig' in config and 'masterCA' not in config['serviceAccountConfig']:
            config['serviceAccountConfig']['masterCA'] = config['oauthConfig'].get('masterCA', 'ca.crt')

        # Add proxyClientInfo to master-config
        if 'proxyClientInfo' not in config['kubernetesMasterConfig']:
            config['kubernetesMasterConfig']['proxyClientInfo'] = {
                'certFile': 'master.proxy-client.crt',
                'keyFile': 'master.proxy-client.key'
            }
            changes.append("master-config.yaml: added proxyClientInfo")

    if len(changes) > 0:
        if backup:
            # TODO: Check success:
            ansible_module.backup_local(config_file)

        write_config(config, config_file)

    return changes


def upgrade_ap_to_ose(role, ansible_module, config_base, backup):
    """Main upgrade method for rhap to ose."""
    changes = []

    # Facts do not get transferred to the hosts where custom modules run,
    # need to make some assumptions here.
    config_file = os.path.join(config_base, role, '{0}-config.yaml'.format(role))
    config = read_config(config_file)

    if role == 'master' and 'disabledFeatures' in config:
        del config['disabledFeatures']

    if 'imageConfig' in config and 'format' in config['imageConfig']:
        img_format = config['imageConfig']['format']
        for img_prefix in ('aep3_beta', 'aep3'):
            if img_prefix in img_format:
                config['imageConfig']['format'] = img_format.replace(img_prefix, 'openshift3').replace('aep', 'openshift')
                changes.append("master-config.yaml: updated imageConfig.format")
                break

    if len(changes) > 0:
        if backup:
            # TODO: Check success:
            ansible_module.backup_local(config_file)

        write_config(config, config_file)

    return changes


def upgrade_config(role, ansible_module, config_base, from_version, to_version, backup):
    """Upgrade entry point."""
    if from_version == '3.0':
        if to_version == '3.1':
            return upgrade_3_0_to_3_1(role, ansible_module, config_base, backup)
    elif from_version == 'rhap':
        if to_version == 'ose':
            return upgrade_ap_to_ose(role, ansible_module, config_base, backup)


def main():
    """ main """
    # disabling pylint errors for global-variable-undefined and invalid-name
    # for 'global module' usage, since it is required to use ansible_facts
    # pylint: disable=global-variable-undefined, invalid-name,
    # redefined-outer-name
    global module

    module = AnsibleModule(
        argument_spec=dict(
            config_base=dict(required=True),
            from_version=dict(required=True, choices=['rhap', '3.0']),
            to_version=dict(required=True, choices=['ose', '3.1']),
            role=dict(required=True, choices=['master', 'node']),
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
        changes = upgrade_config(role, module, config_base, from_version,
                                 to_version, backup)
        changed = len(changes) > 0
        return module.exit_json(changed=changed, changes=changes)

    # ignore broad-except error to avoid stack trace to ansible user
    # pylint: disable=broad-except
    except Exception, e:
        return module.fail_json(msg=str(e))

# ignore pylint errors related to the module_utils import
# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import
# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
