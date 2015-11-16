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

    return ugroups or None

def get_passwd(passwd):
    '''Determine if password is set, if not, return 'zabbix'
    '''
    if passwd:
        return passwd

    return 'zabbix'

def get_usertype(user_type):
    '''
    Determine zabbix user account type
    '''
    if not user_type:
        return None

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
            zbx_server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            zbx_user=dict(default=os.environ.get('ZABBIX_USER', None), type='str'),
            zbx_password=dict(default=os.environ.get('ZABBIX_PASSWORD', None), type='str'),
            zbx_debug=dict(default=False, type='bool'),
            login=dict(default=None, type='str'),
            first_name=dict(default=None, type='str'),
            last_name=dict(default=None, type='str'),
            user_type=dict(default=None, type='str'),
            password=dict(default=None, type='str'),
            update_password=dict(default=False, type='bool'),
            user_groups=dict(default=[], type='list'),
            state=dict(default='present', type='str'),
        ),
        #supports_check_mode=True
    )

    zapi = ZabbixAPI(ZabbixConnection(module.params['zbx_server'],
                                      module.params['zbx_user'],
                                      module.params['zbx_password'],
                                      module.params['zbx_debug']))

    ## before we can create a user media and users with media types we need media
    zbx_class_name = 'user'
    idname = "userid"
    state = module.params['state']

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'output': 'extend',
                                'search': {'alias': module.params['login']},
                                "selectUsrgrps": 'usergrpid',
                               })
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content) or len(content['result']) == 0:
            module.exit_json(changed=False, state="absent")

        content = zapi.get_content(zbx_class_name, 'delete', [content['result'][0][idname]])
        module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':

        params = {'alias': module.params['login'],
                  'passwd': get_passwd(module.params['password']),
                  'usrgrps': get_usergroups(zapi, module.params['user_groups']),
                  'name': module.params['first_name'],
                  'surname': module.params['last_name'],
                  'type': get_usertype(module.params['user_type']),
                 }

        # Remove any None valued params
        _ = [params.pop(key, None) for key in params.keys() if params[key] is None]

        if not exists(content):
            # if we didn't find it, create it
            content = zapi.get_content(zbx_class_name, 'create', params)

            if content.has_key('Error'):
                module.exit_json(failed=True, changed=False, results=content, state='present')

            module.exit_json(changed=True, results=content['result'], state='present')
        # already exists, we need to update it
        # let's compare properties
        differences = {}

        # Update password
        if not module.params['update_password']:
            params.pop('passwd', None)

        zab_results = content['result'][0]
        for key, value in params.items():

            if key == 'usrgrps':
                # this must be done as a list of ordered dictionaries fails comparison
                if not all([_ in value for _ in zab_results[key]]):
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
