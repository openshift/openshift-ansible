#!/usr/bin/env python
'''
ansible module for zabbix triggers
'''
# vim: expandtab:tabstop=4:shiftwidth=4
#
#   Zabbix trigger ansible module
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

def get_deps(zapi, deps):
    ''' get trigger dependencies
    '''
    results = []
    for desc in deps:
        content = zapi.get_content('trigger',
                                   'get',
                                   {'search': {'description': desc},
                                    'expandExpression': True,
                                    'selectDependencies': 'triggerid',
                                   })
        if content.has_key('result'):
            results.append({'triggerid': content['result'][0]['triggerid']})

    return results

def main():
    '''
    Create a trigger in zabbix

    Example:
    "params": {
        "description": "Processor load is too high on {HOST.NAME}",
        "expression": "{Linux server:system.cpu.load[percpu,avg1].last()}>5",
        "dependencies": [
            {
                "triggerid": "14062"
            }
        ]
    },

    '''

    module = AnsibleModule(
        argument_spec=dict(
            server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            user=dict(default=None, type='str'),
            password=dict(default=None, type='str'),
            expression=dict(default=None, type='str'),
            description=dict(default=None, type='str'),
            dependencies=dict(default=[], type='list'),
            priority=dict(default='avg', type='str'),
            debug=dict(default=False, type='bool'),
            state=dict(default='present', type='str'),
        ),
        #supports_check_mode=True
    )

    user = module.params.get('user', os.environ['ZABBIX_USER'])
    passwd = module.params.get('password', os.environ['ZABBIX_PASSWORD'])


    zapi = ZabbixAPI(ZabbixConnection(module.params['server'], user, passwd, module.params['debug']))

    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'trigger'
    idname = "triggerid"
    state = module.params['state']
    description = module.params['description']

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'search': {'description': description},
                                'expandExpression': True,
                                'selectDependencies': 'triggerid',
                               })
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")
        content = zapi.get_content(zbx_class_name, 'delete', [content['result'][0][idname]])
        module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':
        params = {'description': description,
                  'expression':  module.params['expression'],
                  'dependencies': get_deps(zapi, module.params['dependencies']),
                  'priority': get_priority(module.params['priority']),
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
