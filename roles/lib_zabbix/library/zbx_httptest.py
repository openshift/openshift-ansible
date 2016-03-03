#!/usr/bin/env python
'''
 Ansible module for zabbix httpservice
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
from openshift_tools.zbxapi import ZabbixAPI, ZabbixConnection

def exists(content, key='result'):
    ''' Check if key exists in content or the size of content[key] > 0
    '''
    if not content.has_key(key):
        return False

    if not content[key]:
        return False

    return True

def get_authentication_method(auth):
    ''' determine authentication type'''
    rval = 0
    if 'basic' in auth:
        rval = 1
    elif 'ntlm' in auth:
        rval = 2

    return rval

def get_verify_host(verify):
    '''
    get the values for verify_host
    '''
    if verify:
        return 1

    return 0

def get_app_id(zapi, application):
    '''
    get related templates
    '''
    # Fetch templates by name
    content = zapi.get_content('application',
                               'get',
                               {'search': {'name': application},
                                'selectApplications': ['applicationid', 'name']})
    if content.has_key('result'):
        return content['result'][0]['applicationid']

    return None

def get_template_id(zapi, template_name):
    '''
    get related templates
    '''
    # Fetch templates by name
    content = zapi.get_content('template',
                               'get',
                               {'search': {'host': template_name},
                                'selectApplications': ['applicationid', 'name']})
    if content.has_key('result'):
        return content['result'][0]['templateid']

    return None

def get_host_id_by_name(zapi, host_name):
    '''Get host id by name'''
    content = zapi.get_content('host',
                               'get',
                               {'filter': {'name': host_name}})

    return content['result'][0]['hostid']

def get_status(status):
    ''' Determine the status of the web scenario  '''
    rval = 0
    if 'disabled' in status:
        return 1

    return rval

def find_step(idx, step_list):
    ''' find step by index '''
    for step in step_list:
        if str(step['no']) == str(idx):
            return step

    return None

def steps_equal(zab_steps, user_steps):
    '''compare steps returned from zabbix
       and steps passed from user
    '''

    if len(user_steps) != len(zab_steps):
        return False

    for idx in range(1, len(user_steps)+1):

        user = find_step(idx, user_steps)
        zab = find_step(idx, zab_steps)

        for key, value in user.items():
            if str(value) != str(zab[key]):
                return False

    return True

def process_steps(steps):
    '''Preprocess the step parameters'''
    for idx, step in enumerate(steps):
        if not step.has_key('no'):
            step['no'] = idx + 1

    return steps

# The branches are needed for CRUD and error handling
# pylint: disable=too-many-branches
def main():
    '''
    ansible zabbix module for zbx_item
    '''

    module = AnsibleModule(
        argument_spec=dict(
            zbx_server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            zbx_user=dict(default=os.environ.get('ZABBIX_USER', None), type='str'),
            zbx_password=dict(default=os.environ.get('ZABBIX_PASSWORD', None), type='str'),
            zbx_debug=dict(default=False, type='bool'),
            name=dict(default=None, require=True, type='str'),
            agent=dict(default=None, type='str'),
            template_name=dict(default=None, type='str'),
            host_name=dict(default=None, type='str'),
            interval=dict(default=60, type='int'),
            application=dict(default=None, type='str'),
            authentication=dict(default=None, type='str'),
            http_user=dict(default=None, type='str'),
            http_password=dict(default=None, type='str'),
            state=dict(default='present', type='str'),
            status=dict(default='enabled', type='str'),
            steps=dict(default='present', type='list'),
            verify_host=dict(default=False, type='bool'),
            retries=dict(default=1, type='int'),
            headers=dict(default=None, type='dict'),
            query_type=dict(default='filter', choices=['filter', 'search'], type='str'),
        ),
        #supports_check_mode=True
        mutually_exclusive=[['template_name', 'host_name']],
    )

    zapi = ZabbixAPI(ZabbixConnection(module.params['zbx_server'],
                                      module.params['zbx_user'],
                                      module.params['zbx_password'],
                                      module.params['zbx_debug']))

    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'httptest'
    state = module.params['state']
    hostid = None

    # If a template name was passed then accept the template
    if module.params['template_name']:
        hostid = get_template_id(zapi, module.params['template_name'])
    else:
        hostid = get_host_id_by_name(zapi, module.params['host_name'])

    # Fail if a template was not found matching the name
    if not hostid:
        module.exit_json(failed=True,
                         changed=False,
                         results='Error: Could find template or host with name [%s].' %
                         (module.params.get('template_name', module.params['host_name'])),
                         state="Unkown")

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {module.params['query_type']: {'name': module.params['name']},
                                'selectSteps': 'extend',
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

        content = zapi.get_content(zbx_class_name, 'delete', [content['result'][0]['httptestid']])
        module.exit_json(changed=True, results=content['result'], state="absent")

    # Create and Update
    if state == 'present':

        params = {'name': module.params['name'],
                  'hostid': hostid,
                  'agent': module.params['agent'],
                  'retries': module.params['retries'],
                  'steps': process_steps(module.params['steps']),
                  'applicationid': get_app_id(zapi, module.params['application']),
                  'delay': module.params['interval'],
                  'verify_host': get_verify_host(module.params['verify_host']),
                  'status': get_status(module.params['status']),
                  'headers': module.params['headers'],
                  'http_user': module.params['http_user'],
                  'http_password': module.params['http_password'],
                 }


        # Remove any None valued params
        _ = [params.pop(key, None) for key in params.keys() if params[key] is None]

        #******#
        # CREATE
        #******#
        if not exists(content):
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

            if key == 'steps':
                if not steps_equal(zab_results[key], value):
                    differences[key] = value

            elif zab_results[key] != value and zab_results[key] != str(value):
                differences[key] = value

        # We have differences and need to update
        if not differences:
            module.exit_json(changed=False, results=zab_results, state="present")

        differences['httptestid'] = zab_results['httptestid']
        content = zapi.get_content(zbx_class_name, 'update', differences)

        if content.has_key('error'):
            module.exit_json(failed=True, changed=False, results=content['error'], state="present")

        module.exit_json(changed=True, results=content['result'], state="present")

    module.exit_json(failed=True,
                     changed=False,
                     results='Unknown state passed. %s' % state,
                     state="unknown")

# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import, locally-disabled
# import module snippets.  This are required
from ansible.module_utils.basic import *

main()
