#!/usr/bin/env python
'''
 Ansible module for zabbix itservices
'''
# vim: expandtab:tabstop=4:shiftwidth=4
#
#   Zabbix itservice ansible module
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

def get_parent(dependencies):
    '''Put dependencies into the proper update format'''
    rval = None
    for dep in dependencies:
        if dep['relationship'] == 'parent':
            return dep
    return rval

def format_dependencies(dependencies):
    '''Put dependencies into the proper update format'''
    rval = []
    for dep in dependencies:
        rval.append({'dependsOnServiceid': dep['serviceid'],
                     'soft': get_dependency_type(dep['dep_type']),
                    })

    return rval

def get_dependency_type(dep_type):
    '''Determine the dependency type'''
    rval = 0
    if 'soft' == dep_type:
        rval = 1

    return rval

def get_service_id_by_name(zapi, dependencies):
    '''Fetch the service id for an itservice'''
    deps = []
    for dep in dependencies:
        if dep['name'] == 'root':
            deps.append(dep)
            continue

        content = zapi.get_content('service',
                                   'get',
                                   {'filter': {'name': dep['name']},
                                    'selectDependencies': 'extend',
                                   })
        if content.has_key('result') and content['result']:
            dep['serviceid'] = content['result'][0]['serviceid']
            deps.append(dep)

    return deps

def add_dependencies(zapi, service_name, dependencies):
    '''Fetch the service id for an itservice

       Add a dependency on the parent for this current service item.
    '''

    results = get_service_id_by_name(zapi, [{'name': service_name}])

    content = {}
    for dep in dependencies:
        content = zapi.get_content('service',
                                   'adddependencies',
                                   {'serviceid': results[0]['serviceid'],
                                    'dependsOnServiceid': dep['serviceid'],
                                    'soft': get_dependency_type(dep['dep_type']),
                                   })
        if content.has_key('result') and content['result']:
            continue
        else:
            break

    return content

def get_show_sla(inc_sla):
    ''' Determine the showsla paramter
    '''
    rval = 1
    if 'do not cacluate' in inc_sla:
        rval = 0
    return rval

def get_algorithm(inc_algorithm_str):
    '''
    Determine which type algorithm
    '''
    rval = 0
    if 'at least one' in inc_algorithm_str:
        rval = 1
    elif 'all' in inc_algorithm_str:
        rval = 2

    return rval

# The branches are needed for CRUD and error handling
# pylint: disable=too-many-branches
def main():
    '''
    ansible zabbix module for zbx_itservice
    '''

    module = AnsibleModule(
        argument_spec=dict(
            zbx_server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            zbx_user=dict(default=os.environ.get('ZABBIX_USER', None), type='str'),
            zbx_password=dict(default=os.environ.get('ZABBIX_PASSWORD', None), type='str'),
            zbx_debug=dict(default=False, type='bool'),
            name=dict(default=None, type='str'),
            algorithm=dict(default='do not calculate', choices=['do not calculate', 'at least one', 'all'], type='str'),
            show_sla=dict(default='calculate', choices=['do not calculate', 'calculate'], type='str'),
            good_sla=dict(default='99.9', type='float'),
            sort_order=dict(default=1, type='int'),
            state=dict(default='present', type='str'),
            trigger_id=dict(default=None, type='int'),
            dependencies=dict(default=[], type='list'),
            dep_type=dict(default='hard', choices=['hard', 'soft'], type='str'),
        ),
        #supports_check_mode=True
    )

    zapi = ZabbixAPI(ZabbixConnection(module.params['zbx_server'],
                                      module.params['zbx_user'],
                                      module.params['zbx_password'],
                                      module.params['zbx_debug']))

    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'service'
    state = module.params['state']

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'filter': {'name': module.params['name']},
                                'selectDependencies': 'extend',
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

        content = zapi.get_content(zbx_class_name, 'delete', [content['result'][0]['serviceid']])
        module.exit_json(changed=True, results=content['result'], state="absent")

    # Create and Update
    if state == 'present':

        dependencies = get_service_id_by_name(zapi, module.params['dependencies'])
        params = {'name': module.params['name'],
                  'algorithm': get_algorithm(module.params['algorithm']),
                  'showsla': get_show_sla(module.params['show_sla']),
                  'goodsla': module.params['good_sla'],
                  'sortorder': module.params['sort_order'],
                  'triggerid': module.params['trigger_id']
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

            if dependencies:
                content = add_dependencies(zapi, module.params['name'], dependencies)

                if content.has_key('error'):
                    module.exit_json(failed=True, changed=True, results=content['error'], state="present")

            module.exit_json(changed=True, results=content['result'], state='present')


        ########
        # UPDATE
        ########
        params['dependencies'] = dependencies
        differences = {}
        zab_results = content['result'][0]
        for key, value in params.items():

            if key == 'goodsla':
                if float(value) != float(zab_results[key]):
                    differences[key] = value

            elif key == 'dependencies':
                zab_dep_ids = [item['serviceid'] for item in zab_results[key]]
                user_dep_ids = [item['serviceid'] for item in dependencies]
                if set(zab_dep_ids) != set(user_dep_ids):
                    differences[key] = format_dependencies(dependencies)

            elif zab_results[key] != value and zab_results[key] != str(value):
                differences[key] = value

        if not differences:
            module.exit_json(changed=False, results=zab_results, state="present")

        differences['serviceid'] = zab_results['serviceid']
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
