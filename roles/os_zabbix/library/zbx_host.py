#!/usr/bin/env python
# vim: expandtab:tabstop=4:shiftwidth=4
#
#   Zabbix host ansible module
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

from openshift_tools.monitoring.zbxapi import ZabbixAPI

def exists(content, key='result'):
    ''' Check if key exists in content or the size of content[key] > 0
    '''
    if not content.has_key(key):
        return False

    if not content[key]:
        return False

    return True

def main():

    module = AnsibleModule(
        argument_spec=dict(
            server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            user=dict(default=None, type='str'),
            password=dict(default=None, type='str'),
            name=dict(default=None, type='str'),
            host_groups=dict(default=[], type='list'),
            templates=dict(default=[], type='list'),
            interfaces=dict(default=[], type='list'),
            params=dict(),
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

    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'host'
    idname = "hostid"
    name = module.params['name']
    host_groups = module.params['host_groups']
    templates = module.params['templates']
    interfaces = module.params['interfaces']
    params = module.params['params']
    state = module.params['state']

    # Fetch groups by name
    groups = []
    if host_groups:
        for hgr in host_groups:
            content = zapi.get_content('hostgroup', 'get', {'search': {'name': hgr}})
            if content['result']:
                groups.append({'groupid': content['result'][0]['groupid']})

    templs = []
    # Fetch templates by name
    if templates:
        for template_name in templates:
            results = zapi.get_content('template', 'get', {'search': {'host': template_name}})
            if results[0]:
                templs.append({'templateid': content['results'][0]['templateid']})

    if not interfaces:
        # Default interface creation
        interfaces = [
           {'type':  1, # interface type, 1 = agent
            'main':  1, # default interface? 1 = true
            'useip':  1, # default interface? 1 = true
            'ip':  '127.0.0.1', # default interface? 1 = true
            'dns':  '', # dns for host
            'port':  '10050', # port for interface? 10050
           }
       ]

    if not params:
        params = {}

    # selectInterfaces doesn't appear to be working but is needed.
    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'search': {'host': name},
                               'selectGroups': 'groupid',
                               'selectParentTemplates': 'templateid',
                               'selectInterfaces': 'interfaceid',
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
        params['host'] = name
        params['groups'] = groups
        params['templates'] = templs
        params['interfaces'] = interfaces

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

            elif zab_results[key] != value and \
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
 
