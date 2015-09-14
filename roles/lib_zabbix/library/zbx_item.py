#!/usr/bin/env python
'''
 Ansible module for zabbix items
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
from openshift_tools.monitoring.zbxapi import ZabbixAPI, ZabbixConnection

def exists(content, key='result'):
    ''' Check if key exists in content or the size of content[key] > 0
    '''
    if not content.has_key(key):
        return False

    if not content[key]:
        return False

    return True

def get_value_type(value_type):
    '''
    Possible values:
    0 - numeric float;
    1 - character;
    2 - log;
    3 - numeric unsigned;
    4 - text
    '''
    vtype = 0
    if 'int' in value_type:
        vtype = 3
    elif 'char' in value_type:
        vtype = 1
    elif 'str' in value_type:
        vtype = 4

    return vtype

def get_app_ids(application_names, app_name_ids):
    ''' get application ids from names
    '''
    applications = []
    if application_names:
        for app in application_names:
            applications.append(app_name_ids[app])

    return applications

def get_template_id(zapi, template_name):
    '''
    get related templates
    '''
    template_ids = []
    app_ids = {}
    # Fetch templates by name
    content = zapi.get_content('template',
                               'get',
                               {'search': {'host': template_name},
                                'selectApplications': ['applicationid', 'name']})
    if content.has_key('result'):
        template_ids.append(content['result'][0]['templateid'])
        for app in content['result'][0]['applications']:
            app_ids[app['name']] = app['applicationid']

    return template_ids, app_ids

def get_multiplier(inval):
    ''' Determine the multiplier
    '''
    if inval == None or inval == '':
        return None, 0

    rval = None
    try:
        rval = int(inval)
    except ValueError:
        pass

    if rval:
        return rval, 1

    return rval, 0

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
            name=dict(default=None, type='str'),
            key=dict(default=None, type='str'),
            template_name=dict(default=None, type='str'),
            zabbix_type=dict(default=2, type='int'),
            value_type=dict(default='int', type='str'),
            multiplier=dict(default=None, type='str'),
            description=dict(default=None, type='str'),
            units=dict(default=None, type='str'),
            applications=dict(default=None, type='list'),
            state=dict(default='present', type='str'),
        ),
        #supports_check_mode=True
    )

    zapi = ZabbixAPI(ZabbixConnection(module.params['zbx_server'],
                                      module.params['zbx_user'],
                                      module.params['zbx_password'],
                                      module.params['zbx_debug']))

    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'item'
    state = module.params['state']

    templateid, app_name_ids = get_template_id(zapi, module.params['template_name'])

    # Fail if a template was not found matching the name
    if not templateid:
        module.exit_json(failed=True,
                         changed=False,
                         results='Error: Could find template with name %s for item.' % module.params['template_name'],
                         state="Unkown")

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'search': {'key_': module.params['key']},
                                'selectApplications': 'applicationid',
                                'templateids': templateid,
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

        content = zapi.get_content(zbx_class_name, 'delete', [content['result'][0]['itemid']])
        module.exit_json(changed=True, results=content['result'], state="absent")

    # Create and Update
    if state == 'present':

        formula, use_multiplier = get_multiplier(module.params['multiplier'])
        params = {'name': module.params.get('name', module.params['key']),
                  'key_': module.params['key'],
                  'hostid': templateid[0],
                  'type': module.params['zabbix_type'],
                  'value_type': get_value_type(module.params['value_type']),
                  'applications': get_app_ids(module.params['applications'], app_name_ids),
                  'formula': formula,
                  'multiplier': use_multiplier,
                  'description': module.params['description'],
                  'units': module.params['units'],
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
        _ = params.pop('hostid', None)
        differences = {}
        zab_results = content['result'][0]
        for key, value in params.items():

            if key == 'applications':
                app_ids = [item['applicationid'] for item in zab_results[key]]
                if set(app_ids) != set(value):
                    differences[key] = value

            elif zab_results[key] != value and zab_results[key] != str(value):
                differences[key] = value

        if not differences:
            module.exit_json(changed=False, results=zab_results, state="present")

        # We have differences and need to update
        differences['itemid'] = zab_results['itemid']
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
