#!/usr/bin/env python
'''
 Ansible module for zabbix items
'''
# vim: expandtab:tabstop=4:shiftwidth=4
#
#   Zabbix item ansible module
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

def get_value_type(value_type):
    '''
    Possible values:
    0 - numeric float;
    1 - character;
    2 - log;
    3 - numeric unsigned;
    4 - text
    '''
    vtype = 0
    if 'int' in value_type:
        vtype = 3
    elif 'char' in value_type:
        vtype = 1
    elif 'str' in value_type:
        vtype = 4

    return vtype

def get_app_ids(zapi, application_names):
    ''' get application ids from names
    '''
    if isinstance(application_names, str):
        application_names = [application_names]
    app_ids = []
    for app_name in application_names:
        content = zapi.get_content('application', 'get', {'search': {'name': app_name}})
        if content.has_key('result'):
            app_ids.append(content['result'][0]['applicationid'])
    return app_ids

def main():
    '''
    ansible zabbix module for zbx_item
    '''

    module = AnsibleModule(
        argument_spec=dict(
            server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            user=dict(default=None, type='str'),
            password=dict(default=None, type='str'),
            name=dict(default=None, type='str'),
            key=dict(default=None, type='str'),
            template_name=dict(default=None, type='str'),
            zabbix_type=dict(default=2, type='int'),
            value_type=dict(default='int', type='str'),
            applications=dict(default=[], type='list'),
            debug=dict(default=False, type='bool'),
            state=dict(default='present', type='str'),
        ),
        #supports_check_mode=True
    )

    user = module.params.get('user', os.environ['ZABBIX_USER'])
    passwd = module.params.get('password', os.environ['ZABBIX_PASSWORD'])

    zapi = ZabbixAPI(ZabbixConnection(module.params['server'], user, passwd, module.params['debug']))

    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'item'
    idname = "itemid"
    state = module.params['state']
    key = module.params['key']
    template_name = module.params['template_name']

    content = zapi.get_content('template', 'get', {'search': {'host': template_name}})
    templateid = None
    if content['result']:
        templateid = content['result'][0]['templateid']
    else:
        module.exit_json(changed=False,
                         results='Error: Could find template with name %s for item.' % template_name,
                         state="Unkown")

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'search': {'key_': key},
                                'selectApplications': 'applicationid',
                               })

    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")

        content = zapi.get_content(zbx_class_name, 'delete', [content['result'][0][idname]])
        module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':
        params = {'name': module.params.get('name', module.params['key']),
                  'key_': key,
                  'hostid': templateid,
                  'type': module.params['zabbix_type'],
                  'value_type': get_value_type(module.params['value_type']),
                  'applications': get_app_ids(zapi, module.params['applications']),
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

            if zab_results[key] != value and zab_results[key] != str(value):
                differences[key] = value

        if not differences:
            module.exit_json(changed=False, results=zab_results, state="present")

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
