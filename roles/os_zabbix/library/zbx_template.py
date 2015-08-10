#!/usr/bin/env python
'''
Ansible module for template
'''
# vim: expandtab:tabstop=4:shiftwidth=4
#
#   Zabbix template ansible module
#
#
#   Copyright 2015 Red Hat Inc.
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.
#

# pylint: disable=import-error
from openshift_tools.monitoring.zbxapi import ZabbixAPI
from openshift_tools.monitoring.zbxapi import ZabbixConnection

def exists(content, key='result'):
    ''' Check if key exists in content or the size of content[key] > 0
    '''
    if not content.has_key(key):
        return False

    if not content[key]:
        return False

    return True

def main():
    ''' Ansible module for template
    '''

    module = AnsibleModule(
        argument_spec=dict(
            server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            user=dict(default=None, type='str'),
            password=dict(default=None, type='str'),
            name=dict(default=None, type='str'),
            params=dict(default={}),
            debug=dict(default=False, type='bool'),
            state=dict(default='present', type='str'),
        ),
        #supports_check_mode=True
    )

    user = module.params.get('user', os.environ['ZABBIX_USER'])
    passwd = module.params.get('password', os.environ['ZABBIX_PASSWORD'])

    zbc = ZabbixConnection(module.params['server'], user, passwd, module.params['debug'])
    zapi = ZabbixAPI(zbc)

    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'template'
    idname = 'templateid'
    params = module.params['params']
    tname = module.params['name']
    state = module.params['state']
    # get a template, see if it exists
    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'search': {'host': tname},
                                'selectParentTemplates': 'templateid',
                                'selectGroups': 'groupid',
                                #'selectApplications': extend,
                               })
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")
        if not isinstance(params, list) and content['result'][0].has_key(idname):
            content = zapi.get_content(zbx_class_name, 'delete', [content['result'][0][idname]])
        else:
            content = zapi.get_content(zbx_class_name, 'delete', params)
        module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':
        params.update({'groups': module.params.get('groups', [{'groupid': '1'}]),
                       'host': name,
                      })

        if not exists(content):
            # if we didn't find it, create it
            content = zapi.get_content(zbx_class_name, 'create', params)
            module.exit_json(changed=True, results=content['result'], state='present')
        # already exists, we need to update it
        # let's compare properties
        differences = {}
        zab_results = content['result'][0]
        for key, value in params.items():
            if key == 'templates' and zab_results.has_key('parentTemplates'):
                if zab_results['parentTemplates'] != value:
                    differences[key] = value
            elif zab_results[key] != str(value) and zab_results[key] != value:
                differences[key] = value

        if not differences:
            module.exit_json(changed=False, results=content['result'], state="present")

        # We have differences and need to update
        differences[idname] = zab_results[idname]
        content = zapi.get_content(zbx_class_name, 'update', differences)
        module.exit_json(changed=True, results=content['result'], state="present")

    module.exit_json(failed=True,
                     changed=False,
                     results='Unknown state passed. %s' % state,
                     state="unknown")

# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import, locally-disabled
# import module snippets.  This are required
from ansible.module_utils.basic import *

main()
