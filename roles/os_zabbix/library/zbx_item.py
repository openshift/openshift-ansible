#!/usr/bin/env python
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

import os, sys
sys.path.append(os.getcwd())
from zbxapi import ZabbixAPI
#from openshift_tools.monitoring.zbxapi import ZabbixAPI

def exists(content, key='result'):
    ''' Check if key exists in content or the size of content[key] > 0
    '''
    if not content.has_key(key):
        return False

    if not content[key]:
        return False

    return True

def main():

#def item(self, name, key, template_name, zabbix_type=2, vtype='int', interfaceid=None, \
#applications=None, state='present', params=None):

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
            interface_id=dict(default=None, type='str'),
            applications=dict(default=None, type='str'),
            params=dict(default={}, type='dict'),
            debug=dict(default=False, type='bool'),
            state=dict(default='present', type='str'),
        ),
        #supports_check_mode=True
    )

    user = module.params.get('user', None)
    if not user:
        user = os.environ['ZABBIX_USER']

    passwd = module.params.get('password', None)
    if not passwd:
        passwd = os.environ['ZABBIX_PASSWORD']

    api_data = {
        'user': user,
        'password': passwd,
        'server': module.params['server'],
        'verbose': module.params['debug']
    }

    if not user or not passwd or not module.params['server']:
        module.fail_json(msg='Please specify the user, password, and the zabbix server.')

    zapi = ZabbixAPI(api_data)

    '''
    zabbix_type is the type of item.  2 = zabbix_trapper
    "params": {
        "name": "Free disk space on $1",
        "key_": "vfs.fs.size[/home/joe/,free]",
        "hostid": "30074",
        "type": 0,
        "value_type": 3,
        "interfaceid": "30084",
        "applications": [
            "609",
            "610"
        ],
        "delay": 30
    },
    '''
    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'item'
    idname = "itemid"
    params = module.params['params']
    state = module.params['state']
    name = module.params['name']
    key = module.params['key']
    template_name = module.params['template_name']
    zabbix_type = module.params['zabbix_type']
    value_type = module.params['value_type']
    interface_id = module.params['interface_id']
    applications = module.params['applications']

    content = zapi.get_content('template', 'get', {'search': {'host': template_name}})
    templateid = None
    if content['result']:
        templateid = content['result'][0]['templateid']
    else:
        module.exit_json(changed=False, results='Error: Could find template with name %s for item.' % template_name, state="Unkown")

    '''
    Possible values: 
    0 - numeric float; 
    1 - character; 
    2 - log; 
    3 - numeric unsigned; 
    4 - text.
    '''
    vtype = 0
    if 'int' in value_type:
        vtype = 3
    elif 'float' == value_type:
        vtype = 0
    elif 'char' in value_type:
        vtype = 1
    elif value_type == 'string':
        vtype = 4

    if not applications:
        applications = []

    if not params:
        params = {}

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
        if not isinstance(params, list) and content['result'][0].has_key(idname):
            params = [content['result'][0][idname]]

        content = zapi.get_content(zbx_class_name, 'delete', params)
        module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':
        params['name'] = name
        params['key_'] = key
        params['hostid'] =  templateid
        params['type'] = zabbix_type
        params['value_type'] = vtype
        params['applications'] = applications

        if not exists(content):
            # if we didn't find it, create it
            content = zapi.get_content(zbx_class_name, 'create', params)
            module.exit_json(changed=True, results=content['result'], state='present')
        # already exists, we need to update it
        # let's compare properties
        differences = {}
        zab_results = content['result'][0]
        for key, value in params.items():

            if zab_results[key] != value and \
               zab_results[key] != str(value):
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
        
