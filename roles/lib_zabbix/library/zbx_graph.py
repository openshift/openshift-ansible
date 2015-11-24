#!/usr/bin/env python
'''
 Ansible module for zabbix graphs
'''
# vim: expandtab:tabstop=4:shiftwidth=4
#
#   Zabbix graphs ansible module
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

#---
#- hosts: localhost
#  gather_facts: no
#  tasks:
#  - zbx_graph:
#      zbx_server: https://zabbixserver/zabbix/api_jsonrpc.php
#      zbx_user: Admin
#      zbx_password: zabbix
#      name: Test Graph
#      height: 300
#      width: 500
#      graph_items:
#      - item_name: openshift.master.etcd.create.fail
#        color: red
#        line_style: bold
#      - item_name: openshift.master.etcd.create.success
#        color: red
#        line_style: bold
#
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

def get_graph_type(graphtype):
    '''
    Possible values:
    0 - normal;
    1 - stacked;
    2 - pie;
    3 - exploded;
    '''
    gtype = 0
    if 'stacked' in graphtype:
        gtype = 1
    elif 'pie' in graphtype:
        gtype = 2
    elif 'exploded' in graphtype:
        gtype = 3

    return gtype

def get_show_legend(show_legend):
    '''Get the value for show_legend
       0 - hide
       1 - (default) show
    '''
    rval = 1
    if 'hide' == show_legend:
        rval = 0

    return rval

def get_template_id(zapi, template_name):
    '''
    get related templates
    '''
    # Fetch templates by name
    content = zapi.get_content('template',
                               'get',
                               {'filter': {'host': template_name},})

    if content.has_key('result'):
        return content['result'][0]['templateid']

    return None

def get_color(color_in):
    ''' Receive a color and translate it to a hex representation of the color

        Will have a few setup by default
    '''
    colors = {'black': '000000',
              'red': 'FF0000',
              'pink': 'FFC0CB',
              'purple': '800080',
              'orange': 'FFA500',
              'gold': 'FFD700',
              'yellow': 'FFFF00',
              'green': '008000',
              'cyan': '00FFFF',
              'aqua': '00FFFF',
              'blue': '0000FF',
              'brown': 'A52A2A',
              'gray': '808080',
              'grey': '808080',
              'silver': 'C0C0C0',
             }
    if colors.has_key(color_in):
        return colors[color_in]

    return color_in

def get_line_style(style):
    '''determine the line style
    '''
    line_style = {'line': 0,
                  'filled': 1,
                  'bold': 2,
                  'dot': 3,
                  'dashed': 4,
                  'gradient': 5,
                 }

    if line_style.has_key(style):
        return line_style[style]

    return 0

def get_calc_function(func):
    '''Determine the caclulation function'''
    rval = 2 # default to avg
    if 'min' in func:
        rval = 1
    elif 'max' in func:
        rval = 4
    elif 'all' in func:
        rval = 7
    elif 'last' in func:
        rval = 9

    return rval

def get_graph_item_type(gtype):
    '''Determine the graph item type
    '''
    rval = 0 # simple graph type
    if 'sum' in gtype:
        rval = 2

    return rval

def get_graph_items(zapi, gitems):
    '''Get graph items by id'''

    r_items = []
    for item in gitems:
        content = zapi.get_content('item',
                                   'get',
                                   {'filter': {'name': item['item_name']}})
        _ = item.pop('item_name')
        color = get_color(item.pop('color'))
        drawtype = get_line_style(item.get('line_style', 'line'))
        func = get_calc_function(item.get('calc_func', 'avg'))
        g_type = get_graph_item_type(item.get('graph_item_type', 'simple'))

        if content.has_key('result'):
            tmp = {'itemid': content['result'][0]['itemid'],
                   'color': color,
                   'drawtype': drawtype,
                   'calc_fnc': func,
                   'type': g_type,
                  }
            r_items.append(tmp)

    return r_items

def compare_gitems(zabbix_items, user_items):
    '''Compare zabbix results with the user's supplied items
       return True if user_items are equal
       return False if any of the values differ
    '''
    if len(zabbix_items) != len(user_items):
        return False

    for u_item in user_items:
        for z_item in zabbix_items:
            if u_item['itemid'] == z_item['itemid']:
                if not all([str(value) == z_item[key] for key, value in u_item.items()]):
                    return False

    return True

# The branches are needed for CRUD and error handling
# pylint: disable=too-many-branches
def main():
    '''
    ansible zabbix module for zbx_graphs
    '''

    module = AnsibleModule(
        argument_spec=dict(
            zbx_server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            zbx_user=dict(default=os.environ.get('ZABBIX_USER', None), type='str'),
            zbx_password=dict(default=os.environ.get('ZABBIX_PASSWORD', None), type='str'),
            zbx_debug=dict(default=False, type='bool'),
            name=dict(default=None, type='str'),
            height=dict(default=None, type='int'),
            width=dict(default=None, type='int'),
            graph_type=dict(default='normal', type='str'),
            show_legend=dict(default='show', type='str'),
            state=dict(default='present', type='str'),
            graph_items=dict(default=None, type='list'),
        ),
        #supports_check_mode=True
    )

    zapi = ZabbixAPI(ZabbixConnection(module.params['zbx_server'],
                                      module.params['zbx_user'],
                                      module.params['zbx_password'],
                                      module.params['zbx_debug']))

    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'graph'
    state = module.params['state']

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'filter': {'name': module.params['name']},
                                #'templateids': templateid,
                                'selectGraphItems': 'extend',
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

        content = zapi.get_content(zbx_class_name, 'delete', [content['result'][0]['graphid']])
        module.exit_json(changed=True, results=content['result'], state="absent")

    # Create and Update
    if state == 'present':

        params = {'name': module.params['name'],
                  'height': module.params['height'],
                  'width': module.params['width'],
                  'graphtype': get_graph_type(module.params['graph_type']),
                  'show_legend': get_show_legend(module.params['show_legend']),
                  'gitems': get_graph_items(zapi, module.params['graph_items']),
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

            if key == 'gitems':
                if not compare_gitems(zab_results[key], value):
                    differences[key] = value

            elif zab_results[key] != value and zab_results[key] != str(value):
                differences[key] = value

        if not differences:
            module.exit_json(changed=False, results=zab_results, state="present")

        # We have differences and need to update
        differences['graphid'] = zab_results['graphid']
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
