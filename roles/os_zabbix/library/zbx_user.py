#!/usr/bin/env python
'''
ansible module for zabbix users
'''
# vim: expandtab:tabstop=4:shiftwidth=4
#
#   Zabbix user ansible module
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

def get_usergroups(zapi, usergroups):
    ''' Get usergroups
    '''
    ugroups = []
    for ugr in usergroups:
        content = zapi.get_content('usergroup',
                                   'get',
                                   {'search': {'name': ugr},
                                    #'selectUsers': 'userid',
                                    #'getRights': 'extend'
                                   })
        if content['result']:
            ugroups.append({'usrgrpid': content['result'][0]['usrgrpid']})

    return ugroups


def get_usertype(user_type):
    '''
    Determine zabbix user account type
    '''
    utype = 1
    if 'super' in user_type:
        utype = 3
    elif 'admin' in user_type or user_type == 'admin':
        utype = 2

    return utype

def main():
    '''
    ansible zabbix module for users
    '''

    ##def user(self, name, state='present', params=None):

    module = AnsibleModule(
        argument_spec=dict(
            server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            user=dict(default=None, type='str'),
            password=dict(default=None, type='str'),
            alias=dict(default=None, type='str'),
            name=dict(default=None, type='str'),
            surname=dict(default=None, type='str'),
            user_type=dict(default='user', type='str'),
            passwd=dict(default=None, type='str'),
            usergroups=dict(default=None, type='list'),
            debug=dict(default=False, type='bool'),
            state=dict(default='present', type='str'),
        ),
        #supports_check_mode=True
    )

    user = module.params.get('user', os.environ['ZABBIX_USER'])
    password = module.params.get('password', os.environ['ZABBIX_PASSWORD'])

    zapi = ZabbixAPI(ZabbixConnection(module.params['server'], user, password, module.params['debug']))

    ## before we can create a user media and users with media types we need media
    zbx_class_name = 'user'
    idname = "userid"
    alias = module.params['alias']
    state = module.params['state']

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'output': 'extend',
                                'search': {'alias': alias},
                                "selectUsrgrps": 'usergrpid',
                               })
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")

        content = zapi.get_content(zbx_class_name, 'delete', [content['result'][0][idname]])
        module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':
        params = {'alias': alias,
                  'passwd': module.params['passwd'],
                  'usrgrps': get_usergroups(zapi, module.params['usergroups']),
                  'name': module.params['name'],
                  'surname': module.params['surname'],
                  'type': get_usertype(module.params['user_type']),
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
            if key == 'passwd':
                differences[key] = value

            elif zab_results[key] != value and zab_results[key] != str(value):
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
