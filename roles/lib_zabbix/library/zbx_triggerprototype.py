#!/usr/bin/env python
'''
ansible module for zabbix triggerprototypes
'''
# vim: expandtab:tabstop=4:shiftwidth=4
#
#   Zabbix triggerprototypes ansible module
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

def get_priority(priority):
    ''' determine priority
    '''
    prior = 0
    if 'info' in priority:
        prior = 1
    elif 'warn' in priority:
        prior = 2
    elif 'avg' == priority or 'ave' in priority:
        prior = 3
    elif 'high' in priority:
        prior = 4
    elif 'dis' in priority:
        prior = 5

    return prior

def get_trigger_status(inc_status):
    ''' Determine the trigger's status
        0 is enabled
        1 is disabled
    '''
    r_status = 0
    if inc_status == 'disabled':
        r_status = 1

    return r_status


def main():
    '''
    Create a triggerprototype in zabbix
    '''

    module = AnsibleModule(
        argument_spec=dict(
            zbx_server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            zbx_user=dict(default=os.environ.get('ZABBIX_USER', None), type='str'),
            zbx_password=dict(default=os.environ.get('ZABBIX_PASSWORD', None), type='str'),
            zbx_debug=dict(default=False, type='bool'),
            name=dict(default=None, type='str'),
            expression=dict(default=None, type='str'),
            description=dict(default=None, type='str'),
            priority=dict(default='avg', type='str'),
            url=dict(default=None, type='str'),
            status=dict(default=None, type='str'),
            state=dict(default='present', type='str'),
        ),
        #supports_check_mode=True
    )

    zapi = ZabbixAPI(ZabbixConnection(module.params['zbx_server'],
                                      module.params['zbx_user'],
                                      module.params['zbx_password'],
                                      module.params['zbx_debug']))

    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'triggerprototype'
    idname = "triggerid"
    state = module.params['state']
    tname = module.params['name']

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'filter': {'description': tname},
                                'expandExpression': True,
                                'selectDependencies': 'triggerid',
                               })

    # Get
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    # Delete
    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")
        content = zapi.get_content(zbx_class_name, 'delete', [content['result'][0][idname]])
        module.exit_json(changed=True, results=content['result'], state="absent")

    # Create and Update
    if state == 'present':
        params = {'description': tname,
                  'comments':  module.params['description'],
                  'expression':  module.params['expression'],
                  'priority': get_priority(module.params['priority']),
                  'url': module.params['url'],
                  'status': get_trigger_status(module.params['status']),
                 }

        # Remove any None valued params
        _ = [params.pop(key, None) for key in params.keys() if params[key] is None]

        #******#
        # CREATE
        #******#
        if not exists(content):
            # if we didn't find it, create it
            content = zapi.get_content(zbx_class_name, 'create', params)

            if content.has_key('error'):
                module.exit_json(failed=True, changed=True, results=content['error'], state="present")

            module.exit_json(changed=True, results=content['result'], state='present')

        ########
        # UPDATE
        ########
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
