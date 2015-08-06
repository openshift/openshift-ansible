#!/usr/bin/env python
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

from openshift_tools.monitoring.zbxapi import ZabbixAPI

def main():

    ##def usergroup(self, name, rights=None, users=None, state='present', params=None):

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

    user = module.params.get('user', None)
    if not user:
        user = os.environ['ZABBIX_USER']

    passwd = module.params.get('password', None)
    if not passwd:
        passwd = os.environ['ZABBIX_PASSWORD']

    api_data = {
        'user': user,
        'password': passwd,
        'server': module.params['server'],
        'verbose': module.params['debug']
    }

    if not user or not passwd or not module.params['server']:
        module.fail_json(msg='Please specify the user, password, and the zabbix server.')

    zapi = ZabbixAPI(api_data)

    #print "CREATE usergroup"
    #print ezz.usergroup('kenny group', rights=[{'Kenny hostgroup', 'rw'},], state='present', params=None)
