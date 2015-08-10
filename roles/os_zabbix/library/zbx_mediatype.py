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

def main():
    '''
    Ansible zabbix module for mediatype
    '''

    ##def mediatype(self, desc, mtype, smtp_server, smtp_helo='redhat.com', smtp_email='zabbix@openshift.com', ,state='present', params=None):

    module = AnsibleModule(
        argument_spec=dict(
            server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            user=dict(default=None, type='str'),
            password=dict(default=None, type='str'),
            params=dict(),
            debug=dict(default=False, type='bool'),
            state=dict(default='present', type='str'),
        ),
        #supports_check_mode=True
    )

    user = module.params.get('user', os.environ['ZABBIX_USER'])

    passwd = module.params.get('password', os.environ['ZABBIX_PASSWORD'])

    zapi = ZabbixAPI(ZabbixConnection(module.params['server'], user, passwd, module.params['debug']))

    #print "CREATE mediatype"
    #print ezz.mediatype('kenny mediatype desc', state='list', params=None)
    #print "CREATE user"
    #print ezz.user('kenny user', 'zabbix', ['kenny group'], state='present', params=None)
    #media = {
        #'active': True,
        #'mediatype': True,
    #}
    #print ezz.user('kenny user', 'zabbix', ['kenny group'], state='present', params=None)
