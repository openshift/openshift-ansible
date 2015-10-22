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

# This is in place because each module looks similar to each other.
# These need duplicate code as their behavior is very similar
# but different for each zabbix class.
# pylint: disable=duplicate-code

# pylint: disable=import-error
from openshift_tools.monitoring.zbxapi import ZabbixAPI, ZabbixConnection

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
            zbx_server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            zbx_user=dict(default=os.environ.get('ZABBIX_USER', None), type='str'),
            zbx_password=dict(default=os.environ.get('ZABBIX_PASSWORD', None), type='str'),
            zbx_debug=dict(default=False, type='bool'),
            name=dict(default=None, type='str'),
            state=dict(default='present', type='str'),
        ),
        #supports_check_mode=True
    )

    zapi = ZabbixAPI(ZabbixConnection(module.params['zbx_server'],
                                      module.params['zbx_user'],
                                      module.params['zbx_password'],
                                      module.params['zbx_debug']))

    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'template'
    idname = 'templateid'
    tname = module.params['name']
    state = module.params['state']
    # get a template, see if it exists
    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'search': {'host': tname},
                                'selectParentTemplates': 'templateid',
                                'selectGroups': 'groupid',
                                'selectApplications': 'applicationid',
                                'selectDiscoveries': 'extend',
                               })
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")

        if not tname:
            module.exit_json(failed=True,
                             changed=False,
                             results='Must specifiy a template name.',
                             state="absent")

        content = zapi.get_content(zbx_class_name, 'delete', [content['result'][0][idname]])
        module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':
        params = {'groups': module.params.get('groups', [{'groupid': '1'}]),
                  'host': tname,
                 }

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
