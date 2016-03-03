#!/usr/bin/env python
'''
zabbix ansible module for usergroups
'''
# vim: expandtab:tabstop=4:shiftwidth=4
#
#   Zabbix usergroup ansible module
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

# Disabling too-many-branches as we need the error checking and the if-statements
# to determine the proper state
# pylint: disable=too-many-branches

# pylint: disable=import-error
from openshift_tools.zbxapi import ZabbixAPI, ZabbixConnection

def exists(content, key='result'):
    ''' Check if key exists in content or the size of content[key] > 0
    '''
    if not content.has_key(key):
        return False

    if not content[key]:
        return False

    return True

def get_rights(zapi, rights):
    '''Get rights
    '''
    if rights == None:
        return None

    perms = []
    for right in rights:
        hstgrp = right.keys()[0]
        perm = right.values()[0]
        content = zapi.get_content('hostgroup', 'get', {'search': {'name': hstgrp}})
        if content['result']:
            permission = 0
            if perm == 'ro':
                permission = 2
            elif perm == 'rw':
                permission = 3
            perms.append({'id': content['result'][0]['groupid'],
                          'permission': permission})
    return perms

def get_gui_access(access):
    ''' Return the gui_access for a usergroup
    '''
    access = access.lower()
    if access == 'internal':
        return 1
    elif access == 'disabled':
        return 2

    return 0

def get_debug_mode(mode):
    ''' Return the debug_mode for a usergroup
    '''
    mode = mode.lower()
    if mode == 'enabled':
        return 1

    return 0

def get_user_status(status):
    ''' Return the user_status for a usergroup
    '''
    status = status.lower()
    if status == 'enabled':
        return 0

    return 1


def get_userids(zapi, users):
    ''' Get userids from user aliases
    '''
    if not users:
        return None

    userids = []
    for alias in users:
        content = zapi.get_content('user', 'get', {'search': {'alias': alias}})
        if content['result']:
            userids.append(content['result'][0]['userid'])

    return userids

def main():
    ''' Ansible module for usergroup
    '''

    module = AnsibleModule(
        argument_spec=dict(
            zbx_server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            zbx_user=dict(default=os.environ.get('ZABBIX_USER', None), type='str'),
            zbx_password=dict(default=os.environ.get('ZABBIX_PASSWORD', None), type='str'),
            zbx_debug=dict(default=False, type='bool'),
            debug_mode=dict(default='disabled', type='str'),
            gui_access=dict(default='default', type='str'),
            status=dict(default='enabled', type='str'),
            name=dict(default=None, type='str', required=True),
            rights=dict(default=None, type='list'),
            users=dict(default=None, type='list'),
            state=dict(default='present', type='str'),
        ),
        #supports_check_mode=True
    )

    zapi = ZabbixAPI(ZabbixConnection(module.params['zbx_server'],
                                      module.params['zbx_user'],
                                      module.params['zbx_password'],
                                      module.params['zbx_debug']))

    zbx_class_name = 'usergroup'
    idname = "usrgrpid"
    uname = module.params['name']
    state = module.params['state']

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'search': {'name': uname},
                                'selectUsers': 'userid',
                               })
    #******#
    # GET
    #******#
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    #******#
    # DELETE
    #******#
    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")

        if not uname:
            module.exit_json(failed=True, changed=False, results='Need to pass in a user.', state="error")

        content = zapi.get_content(zbx_class_name, 'delete', [content['result'][0][idname]])
        module.exit_json(changed=True, results=content['result'], state="absent")

    # Create and Update
    if state == 'present':

        params = {'name': uname,
                  'rights': get_rights(zapi, module.params['rights']),
                  'users_status': get_user_status(module.params['status']),
                  'gui_access': get_gui_access(module.params['gui_access']),
                  'debug_mode': get_debug_mode(module.params['debug_mode']),
                  'userids': get_userids(zapi, module.params['users']),
                 }

        # Remove any None valued params
        _ = [params.pop(key, None) for key in params.keys() if params[key] == None]

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
            if key == 'rights':
                differences['rights'] = value

            elif key == 'userids' and zab_results.has_key('users'):
                if zab_results['users'] != value:
                    differences['userids'] = value

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
