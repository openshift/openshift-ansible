#!/usr/bin/env python
'''
Zabbix discovery rule ansible module
'''
# vim: expandtab:tabstop=4:shiftwidth=4
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

def get_rule_id(zapi, discoveryrule_name):
    '''get a discoveryrule by name
    '''
    content = zapi.get_content('discoveryrule',
                               'get',
                               {'search': {'name': discoveryrule_name},
                                'output': 'extend',
                               })
    if not content['result']:
        return None
    return content['result'][0]['itemid']

def get_template(zapi, template_name):
    '''get a template by name
    '''
    content = zapi.get_content('template',
                               'get',
                               {'search': {'host': template_name},
                                'output': 'extend',
                                'selectInterfaces': 'interfaceid',
                               })
    if not content['result']:
        return None
    return content['result'][0]

def get_type(ztype):
    '''
    Determine which type of discoverrule this is
    '''
    _types = {'agent': 0,
              'SNMPv1': 1,
              'trapper': 2,
              'simple': 3,
              'SNMPv2': 4,
              'internal': 5,
              'SNMPv3': 6,
              'active': 7,
              'aggregate': 8,
              'external': 10,
              'database monitor': 11,
              'ipmi': 12,
              'ssh': 13,
              'telnet': 14,
              'calculated': 15,
              'JMX': 16,
             }

    for typ in _types.keys():
        if ztype in typ or ztype == typ:
            _vtype = _types[typ]
            break
    else:
        _vtype = 2

    return _vtype

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

def get_status(status):
    ''' Determine status
    '''
    _status = 0
    if status == 'disabled':
        _status = 1
    elif status == 'unsupported':
        _status = 3

    return _status

def get_app_ids(zapi, application_names):
    ''' get application ids from names
    '''
    app_ids = []
    for app_name in application_names:
        content = zapi.get_content('application', 'get', {'search': {'name': app_name}})
        if content.has_key('result'):
            app_ids.append(content['result'][0]['applicationid'])
    return app_ids

def main():
    '''
    Ansible module for zabbix discovery rules
    '''

    module = AnsibleModule(
        argument_spec=dict(
            zbx_server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            zbx_user=dict(default=os.environ.get('ZABBIX_USER', None), type='str'),
            zbx_password=dict(default=os.environ.get('ZABBIX_PASSWORD', None), type='str'),
            zbx_debug=dict(default=False, type='bool'),
            name=dict(default=None, type='str'),
            key=dict(default=None, type='str'),
            interfaceid=dict(default=None, type='int'),
            ztype=dict(default='trapper', type='str'),
            value_type=dict(default='float', type='str'),
            delay=dict(default=60, type='int'),
            lifetime=dict(default=30, type='int'),
            template_name=dict(default=[], type='list'),
            state=dict(default='present', type='str'),
            status=dict(default='enabled', type='str'),
            discoveryrule_name=dict(default=None, type='str'),
            applications=dict(default=[], type='list'),
        ),
        #supports_check_mode=True
    )

    zapi = ZabbixAPI(ZabbixConnection(module.params['zbx_server'],
                                      module.params['zbx_user'],
                                      module.params['zbx_password'],
                                      module.params['zbx_debug']))

    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'itemprototype'
    idname = "itemid"
    dname = module.params['name']
    state = module.params['state']

    # selectInterfaces doesn't appear to be working but is needed.
    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'search': {'name': dname},
                                'selectApplications': 'applicationid',
                                'selectDiscoveryRule': 'itemid',
                                #'selectDhosts': 'dhostid',
                               })
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")

        content = zapi.get_content(zbx_class_name, 'delete', [content['result'][0][idname]])
        module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':
        template = get_template(zapi, module.params['template_name'])
        params = {'name': dname,
                  'key_':  module.params['key'],
                  'hostid':  template['templateid'],
                  'interfaceid': module.params['interfaceid'],
                  'ruleid': get_rule_id(zapi, module.params['discoveryrule_name']),
                  'type': get_type(module.params['ztype']),
                  'value_type': get_value_type(module.params['value_type']),
                  'applications': get_app_ids(zapi, module.params['applications']),
                 }
        if params['type'] in [2, 5, 7, 8, 11, 15]:
            params.pop('interfaceid')

        if not exists(content):
            # if we didn't find it, create it
            content = zapi.get_content(zbx_class_name, 'create', params)
            module.exit_json(changed=True, results=content['result'], state='present')
        # already exists, we need to update it
        # let's compare properties
        differences = {}
        zab_results = content['result'][0]
        for key, value in params.items():

            if key == 'ruleid':
                if value != zab_results['discoveryRule']['itemid']:
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
