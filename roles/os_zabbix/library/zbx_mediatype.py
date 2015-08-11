#!/usr/bin/env python
'''
 Ansible module for mediatype
'''
# vim: expandtab:tabstop=4:shiftwidth=4
#
#   Zabbix mediatype ansible module
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
def get_mtype(mtype):
    '''
    Transport used by the media type.
    Possible values:
    0 - email;
    1 - script;
    2 - SMS;
    3 - Jabber;
    100 - Ez Texting.
    '''
    mtype = mtype.lower()
    media_type = None
    if mtype == 'script':
        media_type = 1
    elif mtype == 'sms':
        media_type = 2
    elif mtype == 'jabber':
        media_type = 3
    elif mtype == 'script':
        media_type = 100
    else:
        media_type = 0

    return media_type

def main():
    '''
    Ansible zabbix module for mediatype
    '''

    module = AnsibleModule(
        argument_spec=dict(
            server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            user=dict(default=None, type='str'),
            password=dict(default=None, type='str'),
            desc=dict(default=None, type='str'),
            mtype=dict(default=None, type='str'),
            smtp_server=dict(default=None, type='str'),
            smtp_helo=dict(default=None, type='str'),
            smtp_email=dict(default=None, type='str'),
            params=dict(default={}, type='dict'),
            debug=dict(default=False, type='bool'),
            state=dict(default='present', type='str'),
        ),
        #supports_check_mode=True
    )

    user = module.params.get('user', os.environ['ZABBIX_USER'])
    passwd = module.params.get('password', os.environ['ZABBIX_PASSWORD'])

    zapi = ZabbixAPI(ZabbixConnection(module.params['server'], user, passwd, module.params['debug']))

    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'mediatype'
    idname = "mediatypeid"
    desc = module.params['desc']
    params = module.params['params']
    state = module.params['state']

    content = zapi.get_content(zbx_class_name, 'get', {'search': {'description': desc}})
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
        params.update({'description': desc,
                       'type': get_mtype(module.params['media_type']),
                       'smtp_server': module.params['smtp_server'],
                       'smtp_helo': module.params['smtp_helo'],
                       'smtp_email': module.params['smtp_email'],
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
