#!/usr/bin/python

import json
import httplib2
import sys
import os
import re
import copy
import pdb

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
        self.username = data.get('username', None)
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

TERMS = ['search', 'output', 'select', 'expand', 'filter']

def diff_content(from_zabbix, from_user, ignore=None):
    ''' Compare passed in object to results returned from zabbix
    '''
    if ignore:
        terms.extend(ignore)
    regex = '(' + '|'.join(TERMS) + ')'
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

def exists(content, key='result'):
    ''' Check if key exists in content or the size of content[key] > 0
    '''
    if not content.has_key(key):
        return False

    if not content[key]:
        return False

    return True

class ZabbixConnection(object):
    '''Zabbix connection object
    '''
    def __init__(self, server, username, password, verbose=False, ssl=False):
        self.server = server
        self.username = username
        self.password = password
        self.verbose = verbose
        self.ssl = ssl

class Zbx(object):
    def __init__(self, zabbix_connection):
        self.zc = zabbix_connection
        self.zapi = ZabbixAPI({'server': self.zc.server,
                               'username': self.zc.username,
                               'password': self.zc.password,
                               'verbose': self.zc.verbose,
                               'ssl': self.zc.ssl,
                              })

    def mediatype(self, desc, smtp_server='admin@openshift.com', mtype='email', smtp_helo='openshift.com', smtp_email='zabbix@openshift.com', state='present', params=None):
        '''
        '''
        #Set the instance and the template for the rest of the calls
        zbx_class_inst = self.zapi.__getattribute__('mediatype')
        zbx_class = self.zapi.__getattribute__('Mediatype')
        idname = "mediatypeid"

        mtype = mtype.lower()
        media_type = None
        if mtype == 'script':
            media_type = 1
        elif mtype == 'sms':
            media_type = 2
        elif mtype == 'jabber':
            media_type = 3
        elif mtype == 'script':
            media_type = 100
        else:
            media_type = 0

        if not params:
            params = {}

        zbx_action_method = zbx_class.__dict__['get']
        _, content = zbx_action_method(zbx_class_inst,
                                       {'search': {'description': desc},
                                       })
        if state == 'list':
            return (False, content['result'], 'list')

        if state == 'absent':
            if not exists(content):
                return (False, content, 'absent')
            if not isinstance(params, list) and content['result'][0].has_key(idname):
                params = [content['result'][0][idname]]

            zbx_action_method = zbx_class.__dict__['delete']
            _, content = zbx_action_method(zbx_class_inst, params)
            return (True, content['result'], 'absent')

        if state == 'present':
            params['description'] = desc
            params['type'] = media_type
            params['smtp_server'] = smtp_server
            params['smtp_helo'] = smtp_helo
            params['smtp_email'] = smtp_email

            if not exists(content):
                # if we didn't find it, create it
                zbx_action_method = zbx_class.__dict__['create']
                _, content = zbx_action_method(zbx_class_inst, params)
                return (True, content['result'], 'present')
            # already exists, we need to update it
            # let's compare properties
            differences = {}
            zab_results = content['result'][0]
            regex = '(' + '|'.join(TERMS) + ')'
            retval = {}
            for key, value in params.items():
                if re.findall(regex, key):
                    continue

                if zab_results[key] != value and \
                   zab_results[key] != str(value):
                    differences[key] = value

            if not differences:
                return(False, zab_results, 'present')

            # We have differences and need to update
            differences[idname] = zab_results[idname]
            zbx_action_method = zbx_class.__dict__['update']
            _, content = zbx_action_method(zbx_class_inst, differences)
            return (True, content, 'present')
        return (False, 'ERROR', 'UNKOWN state')

    def user(self, alias, passwd, user_groups, state='present', params=None):
        '''
        '''
        #Set the instance and the template for the rest of the calls
        zbx_class_inst = self.zapi.__getattribute__('user')
        zbx_class = self.zapi.__getattribute__('User')
        idname = "userid"

        ugroups = []
        if user_groups:
            for ugr in user_groups:
                changed, results, _ = self.usergroup(ugr, state='list')
                if results[0]:
                    ugroups.append({'usrgrpid': results[0]['usrgrpid']})

        if not params:
            params = {}

        zbx_action_method = zbx_class.__dict__['get']
        _, content = zbx_action_method(zbx_class_inst,
                                       {'output': 'extend',
                                        'search': {'alias': alias},
                                        'selectUsrgrps': ['usrgrpid'],
                                       })
        print content
        if state == 'list':
            return (False, content['result'], 'list')

        if state == 'absent':
            if not exists(content):
                return (False, content, 'absent')
            if not isinstance(params, list) and content['result'][0].has_key(idname):
                params = [content['result'][0][idname]]

            zbx_action_method = zbx_class.__dict__['delete']
            _, content = zbx_action_method(zbx_class_inst, params)
            return (True, content['result'], 'absent')

        if state == 'present':
            params['alias'] = alias
            params['passwd'] = passwd
            params['usrgrps'] = ugroups

            if not exists(content):
                # if we didn't find it, create it
                zbx_action_method = zbx_class.__dict__['create']
                _, content = zbx_action_method(zbx_class_inst, params)
                return (True, content['result'], 'present')
            # already exists, we need to update it
            # let's compare properties
            differences = {}
            zab_results = content['result'][0]
            regex = '(' + '|'.join(TERMS) + ')'
            retval = {}
            for key, value in params.items():
                if re.findall(regex, key):
                    continue

                # TODO: NOT PASS IT FOR UPDATE? Error on the side of not updating this
                if key == 'passwd': # and not zab_results.has_key(key):
                    continue
                    #differences[key] = value

                elif zab_results[key] != value and \
                   zab_results[key] != str(value):
                    differences[key] = value

            if not differences:
                return(False, zab_results, 'present')

            # We have differences and need to update
            differences[idname] = zab_results[idname]
            print 
            print zab_results
            print 
            print params
            print 
            print differences
            zbx_action_method = zbx_class.__dict__['update']
            _, content = zbx_action_method(zbx_class_inst, differences)
            return (True, content, 'present')
        return (False, 'ERROR', 'UNKOWN state')

    def usergroup(self, name, rights=None, users=None, state='present', params=None):
        '''
        '''
        #Set the instance and the template for the rest of the calls
        zbx_class_inst = self.zapi.__getattribute__('usergroup')
        zbx_class = self.zapi.__getattribute__('Usergroup')
        idname = "usrgrpid"

        # Fetch groups by name
        perms = []
        if rights:
            for hstgrp, perm in rights:
                changed, results, _ = self.hostgroup(hstgrp, state='list')
                if results[0]:
                    permission = 0
                    if not perm:
                        permission = 0
                    elif perm == 'ro':
                        permission = 2
                    elif perm == 'rw':
                        permission = 3
                    perms.append({'id': results[0]['groupid'],
                                  'permission': permission})

        userids = []
        if users:
            for user in users:
                changed, results, _ = self.user(user, state='list')
                if results[0]:
                    userids.append(results[0]['userid'])

        if not params:
            params = {}

        zbx_action_method = zbx_class.__dict__['get']
        _, content = zbx_action_method(zbx_class_inst,
                                       {'search': {'name': name},
                                        'selectUsers': 'userid',
                                       })
        if state == 'list':
            return (False, content['result'], 'list')

        if state == 'absent':
            if not exists(content):
                return (False, content, 'absent')
            if not isinstance(params, list) and content['result'][0].has_key(idname):
                params = [content['result'][0][idname]]

            zbx_action_method = zbx_class.__dict__['delete']
            _, content = zbx_action_method(zbx_class_inst, params)
            return (True, content['result'], 'absent')

        if state == 'present':
            params['name'] = name
            params['rights'] = perms
            params['userids'] = userids

            if not exists(content):
                # if we didn't find it, create it
                zbx_action_method = zbx_class.__dict__['create']
                _, content = zbx_action_method(zbx_class_inst, params)
                return (True, content['result'], 'present')
            # already exists, we need to update it
            # let's compare properties
            differences = {}
            zab_results = content['result'][0]
            regex = '(' + '|'.join(TERMS) + ')'
            retval = {}
            for key, value in params.items():
                if re.findall(regex, key):
                    continue

                if key == 'rights':
                    differences['rights'] = value

                elif key == 'userids' and zab_results.has_key('users'):
                    if zab_results['users'] != value:
                        differences['userids'] = value

                elif zab_results[key] != value and \
                   zab_results[key] != str(value):
                    differences[key] = value

            if not differences:
                return(False, zab_results, 'present')

            # We have differences and need to update
            differences[idname] = zab_results[idname]
            zbx_action_method = zbx_class.__dict__['update']
            _, content = zbx_action_method(zbx_class_inst, differences)
            return (True, content, 'present')
        return (False, 'ERROR', 'UNKOWN state')

    def hostgroup(self, name, state='present', params=None):
        '''
        '''
        #Set the instance and the template for the rest of the calls
        zbx_class_inst = self.zapi.__getattribute__('hostgroup')
        zbx_class = self.zapi.__getattribute__('Hostgroup')
        idname = "groupid"

        if not params:
            params = {}

        zbx_action_method = zbx_class.__dict__['get']
        _, content = zbx_action_method(zbx_class_inst,
                                       {'search': {'name': name},
                                       })
        if state == 'list':
            return (False, content['result'], 'list')

        if state == 'absent':
            if not exists(content):
                return (False, content, 'absent')
            if not isinstance(params, list) and content['result'][0].has_key(idname):
                params = [content['result'][0][idname]]

            zbx_action_method = zbx_class.__dict__['delete']
            _, content = zbx_action_method(zbx_class_inst, params)
            return (True, content['result'], 'absent')

        if state == 'present':
            params['name'] = name

            if not exists(content):
                # if we didn't find it, create it
                zbx_action_method = zbx_class.__dict__['create']
                _, content = zbx_action_method(zbx_class_inst, params)
                return (True, content['result'], 'present')
            # already exists, we need to update it
            # let's compare properties
            differences = {}
            zab_results = content['result'][0]
            regex = '(' + '|'.join(TERMS) + ')'
            retval = {}
            for key, value in params.items():
                if re.findall(regex, key):
                    continue

                if zab_results[key] != value and \
                   zab_results[key] != str(value):
                    differences[key] = value

            if not differences:
                return(False, zab_results, 'present')

            # We have differences and need to update
            differences[idname] = zab_results[idname]
            zbx_action_method = zbx_class.__dict__['update']
            _, content = zbx_action_method(zbx_class_inst, differences)
            return (True, content, 'present')
        return (False, 'ERROR', 'UNKOWN state')

    def host(self, name, host_groups=None, templates=None, interfaces=None, state='present', params=None):
        '''
        '''
        #Set the instance and the template for the rest of the calls
        zbx_class_inst = self.zapi.__getattribute__('host')
        zbx_class = self.zapi.__getattribute__('Host')
        idname = "hostid"

        # Fetch groups by name
        groups = []
        if host_groups:
            for hgr in host_groups:
                changed, results, _ = self.hostgroup(hgr, state='list')
                if results[0]:
                    groups.append({'groupid': results[0]['groupid']})

        templs = []
        # Fetch templates by name
        if templates:
            for template_name in templates:
                changed, results, _ = self.template(template_name, state='list')
                if results[0]:
                    templs.append({'templateid': results[0]['templateid']})

        if not interfaces:
            interfaces = [
               {'type':  1, # interface type, 1 = agent
                'main':  1, # default interface? 1 = true
                'useip':  1, # default interface? 1 = true
                'ip':  '127.0.0.1', # default interface? 1 = true
                'dns':  '', # dns for host
                'port':  '10050', # port for interface? 10050
               }
           ]
        else:
            interfaces = []

        if not params:
            params = {}

        zbx_action_method = zbx_class.__dict__['get']
        _, content = zbx_action_method(zbx_class_inst,
                                       {'search': {'host': name},
                                       'selectGroups': 'groupid',
                                       'selectParentTemplates': 'templateid',
                                       })
        if state == 'list':
            return (False, content['result'], 'list')

        if state == 'absent':
            if not exists(content):
                return (False, content, 'absent')
            if not isinstance(params, list) and content['result'][0].has_key(idname):
                params = [content['result'][0][idname]]

            zbx_action_method = zbx_class.__dict__['delete']
            _, content = zbx_action_method(zbx_class_inst, params)
            return (True, content['result'], 'absent')

        if state == 'present':
            params['host'] = name
            params['groups'] = groups
            params['templates'] = templs
            params['interfaces'] = interfaces

            if not exists(content):
                # if we didn't find it, create it
                zbx_action_method = zbx_class.__dict__['create']
                _, content = zbx_action_method(zbx_class_inst, params)
                return (True, content['result'], 'present')
            # already exists, we need to update it
            # let's compare properties
            differences = {}
            zab_results = content['result'][0]
            regex = '(' + '|'.join(TERMS) + '|interfaces)'
            retval = {}
            for key, value in params.items():
                if re.findall(regex, key):
                    continue

                if key == 'templates' and zab_results.has_key('parentTemplates'):
                    if zab_results['parentTemplates'] != value:
                        differences[key] = value

                elif zab_results[key] != value and \
                   zab_results[key] != str(value):
                    differences[key] = value

            if not differences:
                return(False, zab_results, 'present')

            # We have differences and need to update
            differences[idname] = zab_results[idname]
            zbx_action_method = zbx_class.__dict__['update']
            _, content = zbx_action_method(zbx_class_inst, differences)
            return (True, content, 'present')
        return (False, 'ERROR', 'UNKOWN state')

    def trigger(self, expression, desc='', dependencies=None, state='present', params=None):
        '''
        "params": {
            "description": "Processor load is too high on {HOST.NAME}",
            "expression": "{Linux server:system.cpu.load[percpu,avg1].last()}>5",
            "dependencies": [
                {
                    "triggerid": "14062"
                }
            ]
        },

        '''
        #Set the instance and the template for the rest of the calls
        zbx_class_inst = self.zapi.__getattribute__('trigger')
        zbx_class = self.zapi.__getattribute__('Trigger')
        idname = "triggerid"

        # need to look up dependencies by expression? description?
        # TODO
        deps = []
        if dependencies:
            for depend_expr in dependencies:
                changed, results, _ = self.trigger(depend_expr)
                if results[0]:
                    deps.append({'triggerid': results[0]['triggerid']})
        else:
            dependencies = []

        if not params:
            params = {}

        zbx_action_method = zbx_class.__dict__['get']
        _, content = zbx_action_method(zbx_class_inst,
                                       {'search': {'description': desc},
                                       'expandExpression': True,
                                       'selectDependencies': 'triggerid',
                                       })
        if state == 'list':
            return (False, content['result'], 'list')

        if state == 'absent':
            if not exists(content):
                return (False, content, 'absent')
            if not isinstance(params, list) and content['result'][0].has_key(idname):
                params = [content['result'][0][idname]]

            zbx_action_method = zbx_class.__dict__['delete']
            _, content = zbx_action_method(zbx_class_inst, params)
            return (True, content['result'], 'absent')

        if state == 'present':
            params['description'] = desc
            params['expression'] = expression
            params['dependencies'] =  dependencies

            if not exists(content):
                # if we didn't find it, create it
                zbx_action_method = zbx_class.__dict__['create']
                _, content = zbx_action_method(zbx_class_inst, params)
                return (True, content['result'], 'present')
            # already exists, we need to update it
            # let's compare properties
            differences = {}
            zab_results = content['result'][0]
            regex = '(' + '|'.join(TERMS) + ')'
            retval = {}
            for key, value in params.items():
                if re.findall(regex, key):
                    continue

                if zab_results[key] != value and \
                   zab_results[key] != str(value):
                    differences[key] = value

            if not differences:
                return(False, zab_results, 'present')

            # We have differences and need to update
            differences[idname] = zab_results[idname]
            zbx_action_method = zbx_class.__dict__['update']
            _, content = zbx_action_method(zbx_class_inst, differences)
            return (True, content, 'present')
        return (False, 'ERROR', 'UNKOWN state')

    def item(self, name, key, templ_name, zabbix_type=2, vtype='int', interfaceid=None, \
             applications=None, state='present', params=None):
        '''
        zabbix_type is the type of item.  2 = zabbix_trapper
        "params": {
            "name": "Free disk space on $1",
            "key_": "vfs.fs.size[/home/joe/,free]",
            "hostid": "30074",
            "type": 0,
            "value_type": 3,
            "interfaceid": "30084",
            "applications": [
                "609",
                "610"
            ],
            "delay": 30
        },
        '''
        #Set the instance and the template for the rest of the calls
        zbx_class_inst = self.zapi.__getattribute__('item')
        zbx_class = self.zapi.__getattribute__('Item')
        idname = "itemid"

        changed, results, _ = self.template(templ_name, state='list')
        templateid = -1
        if results:
            templateid = results[0]['templateid']
        else:
            return (False, None, None)
            #TODO: ERROR, template name not found

        '''
        Possible values: 
        0 - numeric float; 
        1 - character; 
        2 - log; 
        3 - numeric unsigned; 
        4 - text.
        '''
        value_type = 0
        if 'int' in vtype:
            value_type = 3
        elif 'float' in vtype:
            value_type = 0
        elif 'char' in vtype:
            value_type = 1
        elif vtype == 'string':
            value_type = 4

        if not applications:
            applications = []

        if not params:
            params = {}

        zbx_action_method = zbx_class.__dict__['get']
        _, content = zbx_action_method(zbx_class_inst,
                                       {'search': {'key_': key},
                                        'selectApplications': 'applicationid',
                                       })
        if state == 'list':
            return (False, content['result'], 'list')

        if state == 'absent':
            if not exists(content):
                return (False, content, 'absent')
            if not isinstance(params, list) and content['result'][0].has_key(idname):
                params = [content['result'][0][idname]]

            zbx_action_method = zbx_class.__dict__['delete']
            _, content = zbx_action_method(zbx_class_inst, params)
            return (True, content['result'], 'absent')

        if state == 'present':
            params['name'] = name
            params['key_'] = key
            params['hostid'] =  templateid
            params['type'] = zabbix_type
            params['value_type'] = value_type
            params['output'] = 'extend'
            params['applications'] = applications

            if not exists(content):
                # if we didn't find it, create it
                zbx_action_method = zbx_class.__dict__['create']
                _, content = zbx_action_method(zbx_class_inst, params)
                return (True, content['result'], 'present')
            # already exists, we need to update it
            # let's compare properties
            differences = {}
            zab_results = content['result'][0]
            regex = '(' + '|'.join(TERMS) + ')'
            retval = {}
            for key, value in params.items():
                if re.findall(regex, key):
                    continue

                if zab_results[key] != value and \
                   zab_results[key] != str(value):
                    differences[key] = value

            if not differences:
                return(False, zab_results, 'present')

            # We have differences and need to update
            differences[idname] = zab_results[idname]
            zbx_action_method = zbx_class.__dict__['update']
            _, content = zbx_action_method(zbx_class_inst, differences)
            return (True, content, 'present')
        return (False, 'ERROR', 'UNKOWN state')

    def template(self, name, state='present', params=None):
        #Set the instance and the template for the rest of the calls
        zbx_class_inst = self.zapi.__getattribute__('template')
        zbx_class = self.zapi.__getattribute__('Template')
        idname = 'templateid'

        if not params:
            params = {}
        # get a template, see if it exists
        zbx_action_method = zbx_class.__dict__['get']
        _, content = zbx_action_method(zbx_class_inst,
                                       {'search': {'host': name},
                                        'selectParentTemplates': 'templateid',
                                        'selectGroups': 'groupid',
                                        #'selectApplications': extend,
                                       })
        if state == 'list':
            return (False, content['result'], 'list')

        if state == 'absent':
            if not exists(content):
                return (False, content, 'absent')
            if not isinstance(params, list) and content['result'][0].has_key(idname):
                params = [content['result'][0][idname]]

            zbx_action_method = zbx_class.__dict__['delete']
            _, content = zbx_action_method(zbx_class_inst, params)
            return (True, content['result'], 'absent')

        if state == 'present':
            if not exists(content):
                # if we didn't find it, create it
                zbx_action_method = zbx_class.__dict__['create']
                groups = params.get('groups', [])
                params['groups'] = groups
                params['groups'].append({'groupid': 1})
                params['host'] = name
                params['output'] = 'extend'
                _, content = zbx_action_method(zbx_class_inst, params)
                return (True, content['result'], 'present')
            # already exists, we need to update it
            # let's compare properties
            differences = {}
            zab_results = content['result'][0]
            for key, value in params.items():
                if key == 'templates' and zab_results.has_key('parentTemplates'):
                    if zab_results['parentTemplates'] != value:
                        differences[key] = value
                elif zab_results[key] != str(value):
                    differences[key] = str(value)

            if not differences:
                return(False, zab_results, 'present')

            # We have differences and need to update
            differences[idname] = zab_results[idname]
            zbx_action_method = zbx_class.__dict__['update']
            _, content = zbx_action_method(zbx_class_inst, differences)
            return (True, content, 'present')
        return (False, 'ERROR', 'UNKOWN state')

if __name__ == '__main__':
    zc = ZabbixConnection('http://oso-rhel7-zabbix-web.kwoodsontest2.opstest.online.openshift.com/zabbix/api_jsonrpc.php', 'admin', 'zabbix')
    ezz = Zbx(zc)
    #print "CREATE template"
    #print ezz.template('Kenny')
    #print "CREATE item"
    #print ezz.item('Kenny name updated', 'kenny_was_here', 'Kenny', )
    #print "CREATE trigger"
    #print ezz.trigger('{Kenny:kenny_was_here.last()}>2', 'Kenny desc', state='present')
    #print "CREATE hostgroup"
    #print ezz.hostgroup('kenny hostgroup', state='present', params=None)
    #print "CREATE host"
    #print ezz.host('kenny host', host_groups=['kenny hostgroup'], templates=['Kenny'], interfaces=None, state='present', params=None)
    ##def usergroup(self, name, rights=None, users=None, state='present', params=None):
    #print "CREATE usergroup"
    #print ezz.usergroup('kenny group', rights=[{'Kenny hostgroup', 'rw'},], state='present', params=None)
    ##def user(self, name, state='present', params=None):
    ## before we can create a user media and users with media types we need media
    ##def mediatype(self, desc, mtype, smtp_server, smtp_helo='redhat.com', smtp_email='zabbix@openshift.com', ,state='present', params=None):
    #print "CREATE mediatype"
    #print ezz.mediatype('kenny mediatype desc', state='list', params=None)
    #print "CREATE user"
    #print ezz.user('kenny user', 'zabbix', ['kenny group'], state='present', params=None)
    #media = {
        #'active': True,
        #'mediatype': True,
    #}
    #print ezz.user('kenny user', 'zabbix', ['kenny group'], state='present', params=None)
