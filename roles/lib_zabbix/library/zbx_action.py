#!/usr/bin/env python
# vim: expandtab:tabstop=4:shiftwidth=4
'''
 Ansible module for zabbix actions
'''
#
#   Zabbix action ansible module
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
from openshift_tools.monitoring.zbxapi import ZabbixAPI, ZabbixConnection, ZabbixAPIError

CUSTOM_SCRIPT_ACTION = '0'
IPMI_ACTION = '1'
SSH_ACTION = '2'
TELNET_ACTION = '3'
GLOBAL_SCRIPT_ACTION = '4'

EXECUTE_ON_ZABBIX_AGENT = '0'
EXECUTE_ON_ZABBIX_SERVER = '1'

OPERATION_REMOTE_COMMAND = '1'

def exists(content, key='result'):
    ''' Check if key exists in content or the size of content[key] > 0
    '''
    if not content.has_key(key):
        return False

    if not content[key]:
        return False

    return True

def conditions_equal(zab_conditions, user_conditions):
    '''Compare two lists of conditions'''
    c_type = 'conditiontype'
    _op = 'operator'
    val = 'value'
    if len(user_conditions) != len(zab_conditions):
        return False

    for zab_cond, user_cond in zip(zab_conditions, user_conditions):
        if zab_cond[c_type] != str(user_cond[c_type]) or zab_cond[_op] != str(user_cond[_op]) or \
           zab_cond[val] != str(user_cond[val]):
            return False

    return True

def filter_differences(zabbix_filters, user_filters):
    '''Determine the differences from user and zabbix for operations'''
    rval = {}
    for key, val in user_filters.items():

        if key == 'conditions':
            if not conditions_equal(zabbix_filters[key], val):
                rval[key] = val

        elif zabbix_filters[key] != str(val):
            rval[key] = val

    return rval

def opconditions_diff(zab_val, user_val):
    ''' Report whether there are differences between opconditions on
        zabbix and opconditions supplied by user '''

    if len(zab_val) != len(user_val):
        return True

    for z_cond, u_cond in zip(zab_val, user_val):
        if not all([str(u_cond[op_key]) == z_cond[op_key] for op_key in \
                    ['conditiontype', 'operator', 'value']]):
            return True

    return False

def opmessage_diff(zab_val, user_val):
    ''' Report whether there are differences between opmessage on
        zabbix and opmessage supplied by user '''

    for op_msg_key, op_msg_val in user_val.items():
        if zab_val[op_msg_key] != str(op_msg_val):
            return True

    return False

def opmessage_grp_diff(zab_val, user_val):
    ''' Report whether there are differences between opmessage_grp
        on zabbix and opmessage_grp supplied by user '''

    zab_grp_ids = set([ugrp['usrgrpid'] for ugrp in zab_val])
    usr_grp_ids = set([ugrp['usrgrpid'] for ugrp in user_val])
    if usr_grp_ids != zab_grp_ids:
        return True

    return False

def opmessage_usr_diff(zab_val, user_val):
    ''' Report whether there are differences between opmessage_usr
        on zabbix and opmessage_usr supplied by user '''

    zab_usr_ids = set([usr['userid'] for usr in zab_val])
    usr_ids = set([usr['userid'] for usr in user_val])
    if usr_ids != zab_usr_ids:
        return True

    return False

def opcommand_diff(zab_op_cmd, usr_op_cmd):
    ''' Check whether user-provided opcommand matches what's already
        stored in Zabbix '''

    for usr_op_cmd_key, usr_op_cmd_val in usr_op_cmd.items():
        if zab_op_cmd[usr_op_cmd_key] != str(usr_op_cmd_val):
            return True
    return False

def host_in_zabbix(zab_hosts, usr_host):
    ''' Check whether a particular user host is already in the
        Zabbix list of hosts '''

    for usr_hst_key, usr_hst_val in usr_host.items():
        for zab_host in zab_hosts:
            if usr_hst_key in zab_host and \
               zab_host[usr_hst_key] == str(usr_hst_val):
                return True

    return False

def hostlist_in_zabbix(zab_hosts, usr_hosts):
    ''' Check whether user-provided list of hosts are already in
        the Zabbix action '''

    if len(zab_hosts) != len(usr_hosts):
        return False

    for usr_host in usr_hosts:
        if not host_in_zabbix(zab_hosts, usr_host):
            return False

    return True

# We are comparing two lists of dictionaries (the one stored on zabbix and the
# one the user is providing). For each type of operation, determine whether there
# is a difference between what is stored on zabbix and what the user is providing.
# If there is a difference, we take the user-provided data for what needs to
# be stored/updated into zabbix.
def operation_differences(zabbix_ops, user_ops):
    '''Determine the differences from user and zabbix for operations'''

    # if they don't match, take the user options
    if len(zabbix_ops) != len(user_ops):
        return user_ops

    rval = {}
    for zab, user in zip(zabbix_ops, user_ops):
        for oper in user.keys():
            if oper == 'opconditions' and opconditions_diff(zab[oper], \
                                                                user[oper]):
                rval[oper] = user[oper]

            elif oper == 'opmessage' and opmessage_diff(zab[oper], \
                                                        user[oper]):
                rval[oper] = user[oper]

            elif oper == 'opmessage_grp' and opmessage_grp_diff(zab[oper], \
                                                                user[oper]):
                rval[oper] = user[oper]

            elif oper == 'opmessage_usr' and opmessage_usr_diff(zab[oper], \
                                                                user[oper]):
                rval[oper] = user[oper]

            elif oper == 'opcommand' and opcommand_diff(zab[oper], \
                                                        user[oper]):
                rval[oper] = user[oper]

            # opcommand_grp can be treated just like opcommand_hst
            # as opcommand_grp[] is just a list of groups
            elif oper == 'opcommand_hst' or oper == 'opcommand_grp':
                if not hostlist_in_zabbix(zab[oper], user[oper]):
                    rval[oper] = user[oper]

            # if it's any other type of operation than the ones tested above
            # just do a direct compare
            elif oper not in ['opconditions', 'opmessage', 'opmessage_grp',
                              'opmessage_usr', 'opcommand', 'opcommand_hst',
                              'opcommand_grp'] \
                        and str(zab[oper]) != str(user[oper]):
                rval[oper] = user[oper]

    return rval

def get_users(zapi, users):
    '''get the mediatype id from the mediatype name'''
    rval_users = []

    for user in users:
        content = zapi.get_content('user',
                                   'get',
                                   {'filter': {'alias': user}})
        rval_users.append({'userid': content['result'][0]['userid']})

    return rval_users

def get_user_groups(zapi, groups):
    '''get the mediatype id from the mediatype name'''
    user_groups = []

    for group in groups:
        content = zapi.get_content('usergroup',
                                   'get',
                                   {'search': {'name': group}})
        for result in content['result']:
            user_groups.append({'usrgrpid': result['usrgrpid']})

    return user_groups

def get_mediatype_id_by_name(zapi, m_name):
    '''get the mediatype id from the mediatype name'''
    content = zapi.get_content('mediatype',
                               'get',
                               {'filter': {'description': m_name}})

    return content['result'][0]['mediatypeid']

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

def get_event_source(from_src):
    '''Translate even str into value'''
    choices = ['trigger', 'discovery', 'auto', 'internal']
    rval = 0
    try:
        rval = choices.index(from_src)
    except ValueError as _:
        ZabbixAPIError('Value not found for event source [%s]' % from_src)

    return rval

def get_status(inc_status):
    '''determine status for action'''
    rval = 1
    if inc_status == 'enabled':
        rval = 0

    return rval

def get_condition_operator(inc_operator):
    ''' determine the condition operator'''
    vals = {'=': 0,
            '<>': 1,
            'like': 2,
            'not like': 3,
            'in': 4,
            '>=': 5,
            '<=': 6,
            'not in': 7,
           }

    return vals[inc_operator]

def get_host_id_by_name(zapi, host_name):
    '''Get host id by name'''
    content = zapi.get_content('host',
                               'get',
                               {'filter': {'name': host_name}})

    return content['result'][0]['hostid']

def get_trigger_value(inc_trigger):
    '''determine the proper trigger value'''
    rval = 1
    if inc_trigger == 'PROBLEM':
        rval = 1
    else:
        rval = 0

    return rval

def get_template_id_by_name(zapi, t_name):
    '''get the template id by name'''
    content = zapi.get_content('template',
                               'get',
                               {'filter': {'host': t_name}})

    return content['result'][0]['templateid']


def get_host_group_id_by_name(zapi, hg_name):
    '''Get hostgroup id by name'''
    content = zapi.get_content('hostgroup',
                               'get',
                               {'filter': {'name': hg_name}})

    return content['result'][0]['groupid']

def get_condition_type(event_source, inc_condition):
    '''determine the condition type'''
    c_types = {}
    if event_source == 'trigger':
        c_types = {'host group': 0,
                   'host': 1,
                   'trigger': 2,
                   'trigger name': 3,
                   'trigger severity': 4,
                   'trigger value': 5,
                   'time period': 6,
                   'host template': 13,
                   'application': 15,
                   'maintenance status': 16,
                  }

    elif event_source == 'discovery':
        c_types = {'host IP': 7,
                   'discovered service type': 8,
                   'discovered service port': 9,
                   'discovery status': 10,
                   'uptime or downtime duration': 11,
                   'received value': 12,
                   'discovery rule': 18,
                   'discovery check': 19,
                   'proxy': 20,
                   'discovery object': 21,
                  }

    elif event_source == 'auto':
        c_types = {'proxy': 20,
                   'host name': 22,
                   'host metadata': 24,
                  }

    elif event_source == 'internal':
        c_types = {'host group': 0,
                   'host': 1,
                   'host template': 13,
                   'application': 15,
                   'event type': 23,
                  }
    else:
        raise ZabbixAPIError('Unkown event source %s' % event_source)

    return c_types[inc_condition]

def get_operation_type(inc_operation):
    ''' determine the correct operation type'''
    o_types = {'send message': 0,
               'remote command': OPERATION_REMOTE_COMMAND,
               'add host': 2,
               'remove host': 3,
               'add to host group': 4,
               'remove from host group': 5,
               'link to template': 6,
               'unlink from template': 7,
               'enable host': 8,
               'disable host': 9,
              }

    return o_types[inc_operation]

def get_opcommand_type(opcommand_type):
    ''' determine the opcommand type '''
    oc_types = {'custom script': CUSTOM_SCRIPT_ACTION,
                'IPMI': IPMI_ACTION,
                'SSH': SSH_ACTION,
                'Telnet': TELNET_ACTION,
                'global script': GLOBAL_SCRIPT_ACTION,
               }

    return oc_types[opcommand_type]

def get_execute_on(execute_on):
    ''' determine the execution target '''
    e_types = {'zabbix agent': EXECUTE_ON_ZABBIX_AGENT,
               'zabbix server': EXECUTE_ON_ZABBIX_SERVER,
              }

    return e_types[execute_on]

def action_remote_command(ansible_module, zapi, operation):
    ''' Process remote command type of actions '''

    if 'type' not in operation['opcommand']:
        ansible_module.exit_json(failed=True, changed=False, state='unknown',
                                 results="No Operation Type provided")

    operation['opcommand']['type'] = get_opcommand_type(operation['opcommand']['type'])

    if operation['opcommand']['type'] == CUSTOM_SCRIPT_ACTION:

        if 'execute_on' in operation['opcommand']:
            operation['opcommand']['execute_on'] = get_execute_on(operation['opcommand']['execute_on'])

        # custom script still requires the target hosts/groups to be set
        operation['opcommand_hst'] = []
        operation['opcommand_grp'] = []
        for usr_host in operation['target_hosts']:
            if usr_host['target_type'] == 'zabbix server':
                # 0 = target host local/current host
                operation['opcommand_hst'].append({'hostid': 0})
            elif usr_host['target_type'] == 'group':
                group_name = usr_host['target']
                gid = get_host_group_id_by_name(zapi, group_name)
                operation['opcommand_grp'].append({'groupid': gid})
            elif usr_host['target_type'] == 'host':
                host_name = usr_host['target']
                hid = get_host_id_by_name(zapi, host_name)
                operation['opcommand_hst'].append({'hostid': hid})

        # 'target_hosts' is just to make it easier to build zbx_actions
        # not part of ZabbixAPI
        del operation['target_hosts']
    else:
        ansible_module.exit_json(failed=True, changed=False, state='unknown',
                                 results="Unsupported remote command type")


def get_action_operations(ansible_module, zapi, inc_operations):
    '''Convert the operations into syntax for api'''
    for operation in inc_operations:
        operation['operationtype'] = get_operation_type(operation['operationtype'])
        if operation['operationtype'] == 0: # send message.  Need to fix the
            operation['opmessage']['mediatypeid'] = \
             get_mediatype_id_by_name(zapi, operation['opmessage']['mediatypeid'])
            operation['opmessage_grp'] = get_user_groups(zapi, operation.get('opmessage_grp', []))
            operation['opmessage_usr'] = get_users(zapi, operation.get('opmessage_usr', []))
            if operation['opmessage']['default_msg']:
                operation['opmessage']['default_msg'] = 1
            else:
                operation['opmessage']['default_msg'] = 0

        elif operation['operationtype'] == OPERATION_REMOTE_COMMAND:
            action_remote_command(ansible_module, zapi, operation)

        # Handle Operation conditions:
        # Currently there is only 1 available which
        # is 'event acknowledged'.  In the future
        # if there are any added we will need to pass this
        # option to a function and return the correct conditiontype
        if operation.has_key('opconditions'):
            for condition in operation['opconditions']:
                if condition['conditiontype'] == 'event acknowledged':
                    condition['conditiontype'] = 14

                if condition['operator'] == '=':
                    condition['operator'] = 0

                if condition['value'] == 'acknowledged':
                    condition['value'] = 1
                else:
                    condition['value'] = 0


    return inc_operations

def get_operation_evaltype(inc_type):
    '''get the operation evaltype'''
    rval = 0
    if inc_type == 'and/or':
        rval = 0
    elif inc_type == 'and':
        rval = 1
    elif inc_type == 'or':
        rval = 2
    elif inc_type == 'custom':
        rval = 3

    return rval

def get_action_conditions(zapi, event_source, inc_conditions):
    '''Convert the conditions into syntax for api'''

    calc_type = inc_conditions.pop('calculation_type')
    inc_conditions['evaltype'] = get_operation_evaltype(calc_type)
    for cond in inc_conditions['conditions']:

        cond['operator'] = get_condition_operator(cond['operator'])
        # Based on conditiontype we need to set the proper value
        # e.g. conditiontype = hostgroup then the value needs to be a hostgroup id
        # e.g. conditiontype = host the value needs to be a host id
        cond['conditiontype'] = get_condition_type(event_source, cond['conditiontype'])
        if cond['conditiontype'] == 0:
            cond['value'] = get_host_group_id_by_name(zapi, cond['value'])
        elif cond['conditiontype'] == 1:
            cond['value'] = get_host_id_by_name(zapi, cond['value'])
        elif cond['conditiontype'] == 4:
            cond['value'] = get_priority(cond['value'])

        elif cond['conditiontype'] == 5:
            cond['value'] = get_trigger_value(cond['value'])
        elif cond['conditiontype'] == 13:
            cond['value'] = get_template_id_by_name(zapi, cond['value'])
        elif cond['conditiontype'] == 16:
            cond['value'] = ''

    return inc_conditions


def get_send_recovery(send_recovery):
    '''Get the integer value'''
    rval = 0
    if send_recovery:
        rval = 1

    return rval

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
            event_source=dict(default='trigger', choices=['trigger', 'discovery', 'auto', 'internal'], type='str'),
            action_subject=dict(default="{TRIGGER.NAME}: {TRIGGER.STATUS}", type='str'),
            action_message=dict(default="{TRIGGER.NAME}: {TRIGGER.STATUS}\r\n" +
                                "Last value: {ITEM.LASTVALUE}\r\n\r\n{TRIGGER.URL}", type='str'),
            reply_subject=dict(default="{TRIGGER.NAME}: {TRIGGER.STATUS}", type='str'),
            reply_message=dict(default="Trigger: {TRIGGER.NAME}\r\nTrigger status: {TRIGGER.STATUS}\r\n" +
                               "Trigger severity: {TRIGGER.SEVERITY}\r\nTrigger URL: {TRIGGER.URL}\r\n\r\n" +
                               "Item values:\r\n\r\n1. {ITEM.NAME1} ({HOST.NAME1}:{ITEM.KEY1}): " +
                               "{ITEM.VALUE1}\r\n2. {ITEM.NAME2} ({HOST.NAME2}:{ITEM.KEY2}): " +
                               "{ITEM.VALUE2}\r\n3. {ITEM.NAME3} ({HOST.NAME3}:{ITEM.KEY3}): " +
                               "{ITEM.VALUE3}", type='str'),
            send_recovery=dict(default=False, type='bool'),
            status=dict(default=None, type='str'),
            escalation_time=dict(default=60, type='int'),
            conditions_filter=dict(default=None, type='dict'),
            operations=dict(default=None, type='list'),
            state=dict(default='present', type='str'),
        ),
        #supports_check_mode=True
    )

    zapi = ZabbixAPI(ZabbixConnection(module.params['zbx_server'],
                                      module.params['zbx_user'],
                                      module.params['zbx_password'],
                                      module.params['zbx_debug']))

    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'action'
    state = module.params['state']

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'search': {'name': module.params['name']},
                                'selectFilter': 'extend',
                                'selectOperations': 'extend',
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

        content = zapi.get_content(zbx_class_name, 'delete', [content['result'][0]['actionid']])
        module.exit_json(changed=True, results=content['result'], state="absent")

    # Create and Update
    if state == 'present':

        conditions = get_action_conditions(zapi, module.params['event_source'], module.params['conditions_filter'])
        operations = get_action_operations(module, zapi,
                                           module.params['operations'])
        params = {'name': module.params['name'],
                  'esc_period': module.params['escalation_time'],
                  'eventsource': get_event_source(module.params['event_source']),
                  'status': get_status(module.params['status']),
                  'def_shortdata': module.params['action_subject'],
                  'def_longdata': module.params['action_message'],
                  'r_shortdata': module.params['reply_subject'],
                  'r_longdata': module.params['reply_message'],
                  'recovery_msg': get_send_recovery(module.params['send_recovery']),
                  'filter': conditions,
                  'operations': operations,
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

            if key == 'operations':
                ops = operation_differences(zab_results[key], value)
                if ops:
                    differences[key] = ops

            elif key == 'filter':
                filters = filter_differences(zab_results[key], value)
                if filters:
                    differences[key] = filters

            elif zab_results[key] != value and zab_results[key] != str(value):
                differences[key] = value

        if not differences:
            module.exit_json(changed=False, results=zab_results, state="present")

        # We have differences and need to update.
        # action update requires an id, filters, and operations
        differences['actionid'] = zab_results['actionid']
        differences['operations'] = params['operations']
        differences['filter'] = params['filter']
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
