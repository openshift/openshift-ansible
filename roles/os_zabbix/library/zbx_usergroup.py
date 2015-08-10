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

def get_rights(zapi, rights):
    '''Get rights
    '''
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

def get_userids(zapi, users):
    ''' Get userids
    '''
    userids = []
    for user in users:
        content = zapi.get_content('user', 'get', {'search': {'name': user}})
        if content['result']:
            userids.append(content['result']['userid'])

    return userids

def main():
    ''' Ansible module for usergroup
    '''

    ##def usergroup(self, name, rights=None, users=None, state='present', params=None):

    module = AnsibleModule(
        argument_spec=dict(
            server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            user=dict(default=None, type='str'),
            password=dict(default=None, type='str'),
            name=dict(default=None, type='str'),
            rights=dict(default=[], type='list'),
            users=dict(default=[], type='list'),
            params=dict(default={}, type='dict'),
            debug=dict(default=False, type='bool'),
            state=dict(default='present', type='str'),
        ),
        #supports_check_mode=True
    )

    user = module.params.get('user', os.environ['ZABBIX_USER'])
    passwd = module.params.get('password', os.environ['ZABBIX_PASSWORD'])

    zbc = ZabbixConnection(module.params['server'], user, passwd, module.params['debug'])
    zapi = ZabbixAPI(zbc)

    #print "CREATE usergroup"
    #print ezz.usergroup('kenny group', rights=[{'Kenny hostgroup', 'rw'},], state='present', params=None)
    zbx_class_name = 'usergroup'
    idname = "usrgrpid"
    uname = module.params['name']
    params = module.params['params']
    state = module.params['state']

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'search': {'name': uname},
                                'selectUsers': 'userid',
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
        params.update({'name': uname,
                       'rights': get_rights(zapi, module.params['rights']),
                       'userids': get_userids(zapi, module.params['users']),
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
