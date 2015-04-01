#!/usr/bin/env python

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

import json
import httplib2
import sys
import os
import re

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

    def __init__(self, data={}):
        self.server = data['server'] or None
        self.username = data['user'] or None
        self.password = data['password'] or None
        if any(map(lambda value: value == None, [self.server, self.username, self.password])):
            print 'Please specify zabbix server url, username, and password.'
            sys.exit(1)

        self.verbose = data.has_key('verbose')
        self.use_ssl = data.has_key('use_ssl')
        self.auth = None

        for class_name, method_names in self.classes.items():
            #obj = getattr(self, class_name)(self)
            #obj.__dict__
            setattr(self, class_name.lower(), getattr(self, class_name)(self))

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

    def perform(self, method, params):
        '''
        This method calls your zabbix server.

        It requires the following parameters in order for a proper request to be processed:

            jsonrpc - the version of the JSON-RPC protocol used by the API; the Zabbix API implements JSON-RPC version 2.0;
            method - the API method being called;
            params - parameters that will be passed to the API method;
            id - an arbitrary identifier of the request;
            auth - a user authentication token; since we don't have one yet, it's set to null.
        '''
        http_method = "POST"
        if params.has_key("http_method"):
            http_method = params['http_method']

        jsonrpc = "2.0"
        if params.has_key('jsonrpc'):
            jsonrpc = params['jsonrpc']

        rid = 1
        if params.has_key('id'):
            rid = params['id']

        http = None
        if self.use_ssl:
            http = httplib2.Http()
        else:
            http = httplib2.Http( disable_ssl_certificate_validation=True,)

        headers = params.get('headers', {})
        headers["Content-type"] = "application/json"

        body = {
            "jsonrpc": jsonrpc,
            "method":  method,
            "params":  params,
            "id":      rid,
            'auth':    self.auth,
        }

        if method in ['user.login','api.version']:
            del body['auth']

        body = json.dumps(body)

        if self.verbose:
            print body
            print method
            print headers
            httplib2.debuglevel = 1

        response, results = http.request(self.server, http_method, body, headers)

        if self.verbose:
            print response
            print results

        try:
            results = json.loads(results)
        except ValueError as e:
            results = {"error": e.message}

        return response, results

    '''
    This bit of metaprogramming is where the ZabbixAPI subclasses are created.
    For each of ZabbixAPI.classes we create a class from the key and methods
    from the ZabbixAPI.classes values.  We pass a reference to ZabbixAPI class
    to each subclass in order for each to be able to call the perform method.
    '''
    @staticmethod
    def meta(class_name, method_names):
        # This meta method allows a class to add methods to it.
        def meta_method(Class, method_name):
            # This template method is a stub method for each of the subclass
            # methods.
            def template_method(self, **params):
                return self.parent.perform(class_name.lower()+"."+method_name, params)
            template_method.__doc__ = "https://www.zabbix.com/documentation/2.4/manual/api/reference/%s/%s" % (class_name.lower(), method_name)
            template_method.__name__ = method_name
            # this is where the template method is placed inside of the subclass
            # e.g. setattr(User, "create", stub_method)
            setattr(Class, template_method.__name__, template_method)

        # This class call instantiates a subclass. e.g. User
        Class=type(class_name, (object,), { '__doc__': "https://www.zabbix.com/documentation/2.4/manual/api/reference/%s" % class_name.lower() })
        # This init method gets placed inside of the Class 
        # to allow it to be instantiated.  A reference to the parent class(ZabbixAPI)
        # is passed in to allow each class access to the perform method.
        def __init__(self, parent):
            self.parent = parent
        # This attaches the init to the subclass. e.g. Create
        setattr(Class, __init__.__name__, __init__)
        # For each of our ZabbixAPI.classes dict values
        # Create a method and attach it to our subclass.
        # e.g.  'User': ['delete', 'get', 'updatemedia', 'updateprofile',
        #                'update', 'iswritable', 'logout', 'addmedia', 'create',
        #                'login', 'deletemedia', 'isreadable'],
        # User.delete
        # User.get
        for method_name in method_names:
            meta_method(Class, method_name)
        # Return our subclass with all methods attached
        return Class

# Attach all ZabbixAPI.classes to ZabbixAPI class through metaprogramming
for class_name, method_names in ZabbixAPI.classes.items():
    setattr(ZabbixAPI, class_name, ZabbixAPI.meta(class_name, method_names))

def main():

    module = AnsibleModule(
        argument_spec = dict(
            server=dict(default='https://localhost/zabbix/api_jsonrpc.php', type='str'),
            user=dict(default=None, type='str'),
            password=dict(default=None, type='str'),
            zbx_class=dict( choices=ZabbixAPI.classes.keys()),
            #zbx_class=dict(type='str', require=True),
            action=dict(default=None, type='str'),
            params=dict(),
            debug=dict(default=False, type='bool'),
        ),
        #supports_check_mode=True
    )

    user = module.params.get('user', None)
    if not user:
        user = os.environ['ZABBIX_USER']

    pw = module.params.get('password', None)
    if not pw:
        pw = os.environ['ZABBIX_PASSWORD']

    server = module.params['server']

    if module.params['debug']:
        options['debug'] = True

    api_data = {
        'user': user,
        'password': pw,
        'server': server,
    }

    if not user or not pw or not server:
        module.fail_json('Please specify the user, password, and the zabbix server.')

    zapi = ZabbixAPI(api_data)

    zbx_class = module.params.get('zbx_class')
    action = module.params.get('action')
    params = module.params.get('params', {})


    # Get the instance we are trying to call
    zbx_class_inst = zapi.__getattribute__(zbx_class.lower())
    # Get the instance's method we are trying to call
    zbx_action_method = zapi.__getattribute__(zbx_class.capitalize()).__dict__[action]
    # Make the call with the incoming params
    results = zbx_action_method(zbx_class_inst, **params)

    # Results Section
    changed_state = False
    status = results[0]['status']
    if status not in ['200', '201']:
        #changed_state = False
        module.fail_json(msg="Http response: [%s] - Error: %s" % (str(results[0]), results[1]))

    module.exit_json(**{'results': results[1]['result']})

from ansible.module_utils.basic import *

main()
