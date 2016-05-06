#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4

''' modify_yaml ansible module '''

import yaml

DOCUMENTATION = '''
---
module: modify_yaml
short_description: Modify yaml key value pairs
author: Andrew Butcher
requirements: [ ]
'''
EXAMPLES = '''
- modify_yaml:
    dest: /etc/origin/master/master-config.yaml
    yaml_key: 'kubernetesMasterConfig.masterCount'
    yaml_value: 2
'''

def main():
    ''' Modify key (supplied in jinja2 dot notation) in yaml file, setting
        the key to the desired value.
    '''

    # disabling pylint errors for global-variable-undefined and invalid-name
    # for 'global module' usage, since it is required to use ansible_facts
    # pylint: disable=global-variable-undefined, invalid-name,
    # redefined-outer-name
    global module

    module = AnsibleModule(
        argument_spec=dict(
            dest=dict(required=True),
            yaml_key=dict(required=True),
            yaml_value=dict(required=True),
            backup=dict(required=False, default=True, type='bool'),
        ),
        supports_check_mode=True,
    )

    dest = module.params['dest']
    yaml_key = module.params['yaml_key']
    yaml_value = module.safe_eval(module.params['yaml_value'])
    backup = module.params['backup']

    # Represent null values as an empty string.
    # pylint: disable=missing-docstring, unused-argument
    def none_representer(dumper, data):
        return yaml.ScalarNode(tag=u'tag:yaml.org,2002:null', value=u'')
    yaml.add_representer(type(None), none_representer)

    try:
        changes = []

        yaml_file = open(dest)
        yaml_data = yaml.safe_load(yaml_file.read())
        yaml_file.close()

        ptr = yaml_data
        for key in yaml_key.split('.'):
            if key not in ptr and key != yaml_key.split('.')[-1]:
                ptr[key] = {}
            elif key == yaml_key.split('.')[-1]:
                if (key in ptr and module.safe_eval(ptr[key]) != yaml_value) or (key not in ptr):
                    ptr[key] = yaml_value
                    changes.append((yaml_key, yaml_value))
            else:
                ptr = ptr[key]

        if len(changes) > 0:
            if backup:
                module.backup_local(dest)
            yaml_file = open(dest, 'w')
            yaml_string = yaml.dump(yaml_data, default_flow_style=False)
            yaml_string = yaml_string.replace('\'\'', '""')
            yaml_file.write(yaml_string)
            yaml_file.close()

        return module.exit_json(changed=(len(changes) > 0), changes=changes)

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
