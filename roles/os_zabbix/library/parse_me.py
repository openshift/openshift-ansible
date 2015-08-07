#!/usr/bin/env python


import re


lines = open('zbxapi_test.py').readlines()

group = []
fd = None
inside = False
defline = None
for line in lines:
    if re.findall("return \(False, 'ERROR', 'UNKOWN state'\)", line):
        tail = '''
    module.exit_json(failed=True,
                     changed=False,
                     results='Unknown state passed. %s' % state,
                     state="unknown")

# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import, locally-disabled
# import module snippets.  This are required
from ansible.module_utils.basic import *

main()
        '''
        fd.write(tail)
        fd.close()
        inside = False
        
    elif re.findall('def.*\(', line):
        inside = True
        name = line.split('(')[0].split()[1]
        defline = line
        fd = open("zbx_" + name + ".py", 'w+')
        head = '''#!/usr/bin/env python
# vim: expandtab:tabstop=4:shiftwidth=4
#
#   Zabbix %s ansible module
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

def exists(content, key='result'):
    \'\'\' Check if key exists in content or the size of content[key] > 0
    \'\'\'
    if not content.has_key(key):
        return False

    if not content[key]:
        return False

    return True

def main():

%s
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

''' % (name, line)
        fd.write(head)
        #fd.write(line)

    elif inside:
        fd.write(line)


