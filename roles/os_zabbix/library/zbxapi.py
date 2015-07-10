#!/usr/bin/env python
# vim: expandtab:tabstop=4:shiftwidth=4
'''
   ZabbixAPI ansible module
'''

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
#  Purpose: An ansible module to communicate with zabbix.
#

# pylint: disable=line-too-long
# Disabling line length for readability

import json
import httplib2
import sys
import os
import re
import copy

class ZabbixAPIError(Exception):
    '''
        ZabbixAPIError
        Exists to propagate errors up from the api
    '''
    pass

class ZabbixAPI(object):
    '''
        ZabbixAPI class
    '''
    classes = {
        'Action': ['create', 'delete', 'get', 'update'],
        'Alert': ['get'],
        'Application': ['create', 'delete', 'get', 'massadd', 'update'],
        'Configuration': ['export', 'import'],
        'Dcheck': ['get'],
        'Dhost': ['get'],
        'Drule': ['copy', 'create', 'delete', 'get', 'isreadable', 'iswritable', 'update'],
        'Dservice': ['get'],
        'Event': ['acknowledge', 'get'],
        'Graph': ['create', 'delete', 'get', 'update'],
        'Graphitem': ['get'],
        'Graphprototype': ['create', 'delete', 'get', 'update'],
        'History': ['get'],
        'Hostgroup': ['create', 'delete', 'get', 'isreadable', 'iswritable', 'massadd', 'massremove', 'massupdate', 'update'],
        'Hostinterface': ['create', 'delete', 'get', 'massadd', 'massremove', 'replacehostinterfaces', 'update'],
        'Host': ['create', 'delete', 'get', 'isreadable', 'iswritable', 'massadd', 'massremove', 'massupdate', 'update'],
        'Hostprototype': ['create', 'delete', 'get', 'isreadable', 'iswritable', 'update'],
        'Httptest': ['create', 'delete', 'get', 'isreadable', 'iswritable', 'update'],
        'Iconmap': ['create', 'delete', 'get', 'isreadable', 'iswritable', 'update'],
        'Image': ['create', 'delete', 'get', 'update'],
        'Item': ['create', 'delete', 'get', 'isreadable', 'iswritable', 'update'],
        'Itemprototype': ['create', 'delete', 'get', 'isreadable', 'iswritable', 'update'],
        'Maintenance': ['create', 'delete', 'get', 'update'],
        'Map': ['create', 'delete', 'get', 'isreadable', 'iswritable', 'update'],
        'Mediatype': ['create', 'delete', 'get', 'update'],
        'Proxy': ['create', 'delete', 'get', 'isreadable', 'iswritable', 'update'],
        'Screen': ['create', 'delete', 'get', 'update'],
        'Screenitem': ['create', 'delete', 'get', 'isreadable', 'iswritable', 'update', 'updatebyposition'],
        'Script': ['create', 'delete', 'execute', 'get', 'getscriptsbyhosts', 'update'],
        'Service': ['adddependencies', 'addtimes', 'create', 'delete', 'deletedependencies', 'deletetimes', 'get', 'getsla', 'isreadable', 'iswritable', 'update'],
        'Template': ['create', 'delete', 'get', 'isreadable', 'iswritable', 'massadd', 'massremove', 'massupdate', 'update'],
        'Templatescreen': ['copy', 'create', 'delete', 'get', 'isreadable', 'iswritable', 'update'],
        'Templatescreenitem': ['get'],
        'Trigger': ['adddependencies', 'create', 'delete', 'deletedependencies', 'get', 'isreadable', 'iswritable', 'update'],
        'Triggerprototype': ['create', 'delete', 'get', 'update'],
        'User': ['addmedia', 'create', 'delete', 'deletemedia', 'get', 'isreadable', 'iswritable', 'login', 'logout', 'update', 'updatemedia', 'updateprofile'],
        'Usergroup': ['create', 'delete', 'get', 'isreadable', 'iswritable', 'massadd', 'massupdate', 'update'],
        'Usermacro': ['create', 'createglobal', 'delete', 'deleteglobal', 'get', 'update', 'updateglobal'],
        'Usermedia': ['get'],
    }

    def __init__(self, data=None):
        if not data:
            data = {}
        self.server = data.get('server', None)
        self.username = data.get('user', None)
        self.password = data.get('password', None)
        if any([value == None for value in [self.server, self.username, self.password]]):
            print 'Please specify zabbix server url, username, and password.'
            sys.exit(1)

        self.verbose = data.get('verbose', False)
        self.use_ssl = data.has_key('use_ssl')
        self.auth = None

        for cname, _ in self.classes.items():
            setattr(self, cname.lower(), getattr(self, cname)(self))

        # pylint: disable=no-member
        # This method does not exist until the metaprogramming executed
        results = self.user.login(user=self.username, password=self.password)

        if results[0]['status'] == '200':
            if results[1].has_key('result'):
                self.auth = results[1]['result']
            elif results[1].has_key('error'):
                print "Unable to authenticate with zabbix server. {0} ".format(results[1]['error'])
                sys.exit(1)
        else:
            print "Error in call to zabbix. Http status: {0}.".format(results[0]['status'])
            sys.exit(1)

    def perform(self, method, rpc_params):
        '''
        This method calls your zabbix server.

        It requires the following parameters in order for a proper request to be processed:
            jsonrpc - the version of the JSON-RPC protocol used by the API;
                      the Zabbix API implements JSON-RPC version 2.0;
            method - the API method being called;
            rpc_params - parameters that will be passed to the API method;
            id - an arbitrary identifier of the request;
            auth - a user authentication token; since we don't have one yet, it's set to null.
        '''
        http_method = "POST"
        jsonrpc = "2.0"
        rid = 1

        http = None
        if self.use_ssl:
            http = httplib2.Http()
        else:
            http = httplib2.Http(disable_ssl_certificate_validation=True,)

        headers = {}
        headers["Content-type"] = "application/json"

        body = {
            "jsonrpc": jsonrpc,
            "method":  method,
            "params":  rpc_params.get('params', {}),
            "id":      rid,
            'auth':    self.auth,
        }

        if method in ['user.login', 'api.version']:
            del body['auth']

        body = json.dumps(body)

        if self.verbose:
            print body
            print method
            print headers
            httplib2.debuglevel = 1

        response, content = http.request(self.server, http_method, body, headers)

        if response['status'] not in ['200', '201']:
            raise ZabbixAPIError('Error calling zabbix.  Zabbix returned %s' % response['status'])

        if self.verbose:
            print response
            print content

        try:
            content = json.loads(content)
        except ValueError as err:
            content = {"error": err.message}

        return response, content

    @staticmethod
    def meta(cname, method_names):
        '''
        This bit of metaprogramming is where the ZabbixAPI subclasses are created.
        For each of ZabbixAPI.classes we create a class from the key and methods
        from the ZabbixAPI.classes values.  We pass a reference to ZabbixAPI class
        to each subclass in order for each to be able to call the perform method.
        '''
        def meta_method(_class, method_name):
            '''
            This meta method allows a class to add methods to it.
            '''
            # This template method is a stub method for each of the subclass
            # methods.
            def template_method(self, params=None, **rpc_params):
                '''
                This template method is a stub method for each of the subclass methods.
                '''
                if params:
                    rpc_params['params'] = params
                else:
                    rpc_params['params'] = copy.deepcopy(rpc_params)

                return self.parent.perform(cname.lower()+"."+method_name, rpc_params)

            template_method.__doc__ = \
              "https://www.zabbix.com/documentation/2.4/manual/api/reference/%s/%s" % \
              (cname.lower(), method_name)
            template_method.__name__ = method_name
            # this is where the template method is placed inside of the subclass
            # e.g. setattr(User, "create", stub_method)
            setattr(_class, template_method.__name__, template_method)

        # This class call instantiates a subclass. e.g. User
        _class = type(cname,
                      (object,),
                      {'__doc__': \
                      "https://www.zabbix.com/documentation/2.4/manual/api/reference/%s" % cname.lower()})
        def __init__(self, parent):
            '''
            This init method gets placed inside of the _class
            to allow it to be instantiated.  A reference to the parent class(ZabbixAPI)
            is passed in to allow each class access to the perform method.
            '''
            self.parent = parent

        # This attaches the init to the subclass. e.g. Create
        setattr(_class, __init__.__name__, __init__)
        # For each of our ZabbixAPI.classes dict values
        # Create a method and attach it to our subclass.
        # e.g.  'User': ['delete', 'get', 'updatemedia', 'updateprofile',
        #                'update', 'iswritable', 'logout', 'addmedia', 'create',
        #                'login', 'deletemedia', 'isreadable'],
        # User.delete
        # User.get
        for method_name in method_names:
            meta_method(_class, method_name)
        # Return our subclass with all methods attached
        return _class

# Attach all ZabbixAPI.classes to ZabbixAPI class through metaprogramming
for _class_name, _method_names in ZabbixAPI.classes.items():
    setattr(ZabbixAPI, _class_name, ZabbixAPI.meta(_class_name, _method_names))

def exists(content, key='result'):
    ''' Check if key exists in content or the size of content[key] > 0
    '''
    if not content.has_key(key):
        return False

    if not content[key]:
        return False

    return True

def diff_content(from_zabbix, from_user, ignore=None):
    ''' Compare passed in object to results returned from zabbix
    '''
    terms = ['search', 'output', 'groups', 'select', 'expand', 'filter']
    if ignore:
        terms.extend(ignore)
    regex = '(' + '|'.join(terms) + ')'
    retval = {}
    for key, value in from_user.items():
        if re.findall(regex, key):
            continue

        # special case here for templates.  You query templates and
        # the zabbix api returns parentTemplates.  These will obviously fail.
        # So when its templates compare against parentTemplates.
        if key == 'templates' and from_zabbix.has_key('parentTemplates'):
            if from_zabbix['parentTemplates'] != value:
                retval[key] = value

        elif from_zabbix[key] != str(value):
            retval[key] = str(value)

    return retval

def main():
    '''
    This main method runs the ZabbixAPI Ansible Module
    '''

    module = AnsibleModule(
        argument_spec=dict(
            server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            user=dict(default=None, type='str'),
            password=dict(default=None, type='str'),
            zbx_class=dict(choices=ZabbixAPI.classes.keys()),
            params=dict(),
            debug=dict(default=False, type='bool'),
            state=dict(default='present', type='str'),
            ignore=dict(default=None, type='list'),
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

    ignore = module.params['ignore']
    zbx_class = module.params.get('zbx_class')
    rpc_params = module.params.get('params', {})
    state = module.params.get('state')


    # Get the instance we are trying to call
    zbx_class_inst = zapi.__getattribute__(zbx_class.lower())

    # perform get
    # Get the instance's method we are trying to call

    zbx_action_method = zapi.__getattribute__(zbx_class.capitalize()).__dict__['get']
    _, content = zbx_action_method(zbx_class_inst, rpc_params)

    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")
        # If we are coming from a query, we need to pass in the correct rpc_params for delete.
        # specifically the zabbix class name + 'id'
        # if rpc_params is a list then we need to pass it. (list of ids to delete)
        idname = zbx_class.lower() + "id"
        if not isinstance(rpc_params, list) and content['result'][0].has_key(idname):
            rpc_params = [content['result'][0][idname]]

        zbx_action_method = zapi.__getattribute__(zbx_class.capitalize()).__dict__['delete']
        _, content = zbx_action_method(zbx_class_inst, rpc_params)
        module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':
    # It's not there, create it!
        if not exists(content):
            zbx_action_method = zapi.__getattribute__(zbx_class.capitalize()).__dict__['create']
            _, content = zbx_action_method(zbx_class_inst, rpc_params)
            module.exit_json(changed=True, results=content['result'], state='present')

    # It's there and the same, do nothing!
        diff_params = diff_content(content['result'][0], rpc_params, ignore)
        if not diff_params:
            module.exit_json(changed=False, results=content['result'], state="present")

        # Add the id to update with
        idname = zbx_class.lower() + "id"
        diff_params[idname] = content['result'][0][idname]


        ## It's there and not the same, update it!
        zbx_action_method = zapi.__getattribute__(zbx_class.capitalize()).__dict__['update']
        _, content = zbx_action_method(zbx_class_inst, diff_params)
        module.exit_json(changed=True, results=content, state="present")

    module.exit_json(failed=True,
                     changed=False,
                     results='Unknown state passed. %s' % state,
                     state="unknown")

# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import, locally-disabled
# import module snippets.  This are required
from ansible.module_utils.basic import *

main()

