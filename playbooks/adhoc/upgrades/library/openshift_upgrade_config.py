#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4

import os
import shutil
import yaml

from datetime import datetime

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

def get_cfg_dir():
    cfg_path = '/etc/origin/'
    if not os.path.exists(cfg_path):
        cfg_path = '/etc/openshift/'
    return cfg_path


def upgrade_master_3_0_to_3_1(backup):
    changed = False

    # Facts do not get transferred to the hosts where custom modules run,
    # need to make some assumptions here.
    master_config = os.path.join(get_cfg_dir(), 'master/master-config.yaml')

    f = open(master_config, 'r')
    config = yaml.safe_load(f.read())
    f.close()

    # Remove v1beta3 from apiLevels:
    if 'apiLevels' in config and \
        'v1beta3' in config['apiLevels']:
            config['apiLevels'].remove('v1beta3')
            changed = True
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

    if changed:
        if backup:
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            basedir = os.path.split(master_config)[0]
            backup_file = os.path.join(basedir, 'master-config.yaml.bak-%s'
                % timestamp)
            shutil.copyfile(master_config, backup_file)
        # Write the modified config:
        out_file = open(master_config, 'w')
        out_file.write(yaml.safe_dump(config, default_flow_style=False))
        out_file.close()

    return changed


def upgrade_master(from_version, to_version, backup):
    if from_version == '3.0':
        if to_version == '3.1':
            return upgrade_master_3_0_to_3_1(backup)


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

    from_version = module.params['from_version']
    to_version = module.params['to_version']
    role = module.params['role']
    backup = module.params['backup']

    changed = False
    if role == 'master':
        changed = upgrade_master(from_version, to_version, backup)

    return module.exit_json(changed=changed)

# ignore pylint errors related to the module_utils import
# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import
# import module snippets
from ansible.module_utils.basic import *

if __name__ == '__main__':
    main()
