#!/usr/bin/env python
'''
 Ansible module for user media
'''
# vim: expandtab:tabstop=4:shiftwidth=4
#
#   Zabbix user media  ansible module
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

def get_mtype(zapi, mtype):
    '''Get mediatype

       If passed an int, return it as the mediatypeid
       if its a string, then try to fetch through a description
    '''
    if isinstance(mtype, int):
        return mtype
    try:
        return int(mtype)
    except ValueError:
        pass

    content = zapi.get_content('mediatype', 'get', {'filter': {'description': mtype}})
    if content.has_key('result') and content['result']:
        return content['result'][0]['mediatypeid']

    return None

def get_user(zapi, user):
    ''' Get userids from user aliases
    '''
    content = zapi.get_content('user', 'get', {'filter': {'alias': user}})
    if content['result']:
        return content['result'][0]

    return None

def get_severity(severity):
    ''' determine severity
    '''
    if isinstance(severity, int) or \
       isinstance(severity, str):
        return severity

    val = 0
    sev_map = {
        'not': 2**0,
        'inf': 2**1,
        'war': 2**2,
        'ave':  2**3,
        'avg':  2**3,
        'hig': 2**4,
        'dis': 2**5,
    }
    for level in severity:
        val |= sev_map[level[:3].lower()]
    return val

def get_zbx_user_query_data(zapi, user_name):
    ''' If name exists, retrieve it, and build query params.
    '''
    query = {}
    if user_name:
        zbx_user = get_user(zapi, user_name)
        query = {'userid': zbx_user['userid']}

    return query

def find_media(medias, user_media):
    ''' Find the user media in the list of medias
    '''
    for media in medias:
        if all([media[key] == str(user_media[key]) for key in user_media.keys()]):
            return media
    return None

def get_active(is_active):
    '''Determine active value
       0 - enabled
       1 - disabled
    '''
    active = 1
    if is_active:
        active = 0

    return active

def get_mediatype(zapi, mediatype, mediatype_desc):
    ''' Determine mediatypeid
    '''
    mtypeid = None
    if mediatype:
        mtypeid = get_mtype(zapi, mediatype)
    elif mediatype_desc:
        mtypeid = get_mtype(zapi, mediatype_desc)

    return mtypeid

def preprocess_medias(zapi, medias):
    ''' Insert the correct information when processing medias '''
    for media in medias:
        # Fetch the mediatypeid from the media desc (name)
        if media.has_key('mediatype'):
            media['mediatypeid'] = get_mediatype(zapi, mediatype=None, mediatype_desc=media.pop('mediatype'))

        media['active'] = get_active(media.get('active'))
        media['severity'] = int(get_severity(media['severity']))

    return medias

# Disabling branching as the logic requires branches.
# I've also added a few safeguards which required more branches.
# pylint: disable=too-many-branches
def main():
    '''
    Ansible zabbix module for mediatype
    '''

    module = AnsibleModule(
        argument_spec=dict(
            zbx_server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            zbx_user=dict(default=os.environ.get('ZABBIX_USER', None), type='str'),
            zbx_password=dict(default=os.environ.get('ZABBIX_PASSWORD', None), type='str'),
            zbx_debug=dict(default=False, type='bool'),
            login=dict(default=None, type='str'),
            active=dict(default=False, type='bool'),
            medias=dict(default=None, type='list'),
            mediaid=dict(default=None, type='int'),
            mediatype=dict(default=None, type='str'),
            mediatype_desc=dict(default=None, type='str'),
            #d-d,hh:mm-hh:mm;d-d,hh:mm-hh:mm...
            period=dict(default=None, type='str'),
            sendto=dict(default=None, type='str'),
            severity=dict(default=None, type='str'),
            state=dict(default='present', type='str'),
        ),
        #supports_check_mode=True
    )

    zapi = ZabbixAPI(ZabbixConnection(module.params['zbx_server'],
                                      module.params['zbx_user'],
                                      module.params['zbx_password'],
                                      module.params['zbx_debug']))

    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'user'
    idname = "mediaid"
    state = module.params['state']

    # User media is fetched through the usermedia.get
    zbx_user_query = get_zbx_user_query_data(zapi, module.params['login'])
    content = zapi.get_content('usermedia', 'get',
                               {'userids': [uid for user, uid in zbx_user_query.items()]})
    #####
    # Get
    #####
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    ########
    # Delete
    ########
    if state == 'absent':
        if not exists(content) or len(content['result']) == 0:
            module.exit_json(changed=False, state="absent")

        if not module.params['login']:
            module.exit_json(failed=True, changed=False, results='Must specifiy a user login.', state="absent")

        content = zapi.get_content(zbx_class_name, 'deletemedia', [res[idname] for res in content['result']])

        if content.has_key('error'):
            module.exit_json(changed=False, results=content['error'], state="absent")

        module.exit_json(changed=True, results=content['result'], state="absent")

    # Create and Update
    if state == 'present':
        active = get_active(module.params['active'])
        mtypeid = get_mediatype(zapi, module.params['mediatype'], module.params['mediatype_desc'])

        medias = module.params['medias']
        if medias == None:
            medias = [{'mediatypeid': mtypeid,
                       'sendto': module.params['sendto'],
                       'active': active,
                       'severity': int(get_severity(module.params['severity'])),
                       'period': module.params['period'],
                      }]
        else:
            medias = preprocess_medias(zapi, medias)

        params = {'users': [zbx_user_query],
                  'medias': medias,
                  'output': 'extend',
                 }

        ########
        # Create
        ########
        if not exists(content):
            if not params['medias']:
                module.exit_json(changed=False, results=content['result'], state='present')

            # if we didn't find it, create it
            content = zapi.get_content(zbx_class_name, 'addmedia', params)

            if content.has_key('error'):
                module.exit_json(failed=True, changed=False, results=content['error'], state="present")

            module.exit_json(changed=True, results=content['result'], state='present')

        # mediaid signifies an update
        # If user params exists, check to see if they already exist in zabbix
        # if they exist, then return as no update
        # elif they do not exist, then take user params only
        ########
        # Update
        ########
        diff = {'medias': [], 'users': {}}
        _ = [diff['medias'].append(media) for media in params['medias'] if not find_media(content['result'], media)]

        if not diff['medias']:
            module.exit_json(changed=False, results=content['result'], state="present")

        for user in params['users']:
            diff['users']['userid'] = user['userid']

        # Medias have no real unique key so therefore we need to make it like the incoming user's request
        diff['medias'] = medias

        # We have differences and need to update
        content = zapi.get_content(zbx_class_name, 'updatemedia', diff)

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
