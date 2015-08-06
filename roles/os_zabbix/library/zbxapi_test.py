def mediatype(self, desc, smtp_server='admin@openshift.com', mtype='email', smtp_helo='openshift.com', smtp_email='zabbix@openshift.com', state='present', params=None):
    '''
    '''
    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'mediatype'
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


    content = zapi.get_content(zbx_class_name, 'get', {'search': {'description': desc}})
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")
        if not isinstance(params, list) and content['result'][0].has_key(idname):
            params = [content['result'][0][idname]]

        content = zapi.get_content(zbx_class_name, 'delete', params)
        module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':
        params['description'] = desc
        params['type'] = media_type
        params['smtp_server'] = smtp_server
        params['smtp_helo'] = smtp_helo
        params['smtp_email'] = smtp_email

        if not exists(content):
            # if we didn't find it, create it
            content = zapi.get_content(zbx_class_name, 'create', params)
            module.exit_json(changed=True, results=content['result'], state='present')
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
            module.exit_json(changed=False, results=zab_results, state="present")

        # We have differences and need to update
        differences[idname] = zab_results[idname]
        content = zapi.get_content(zbx_class_name, 'update', differences)
        module.exit_json(changed=True, results=content['result'], state="present")
    return (False, 'ERROR', 'UNKOWN state')

def user(self, alias, passwd, user_groups, state='present', params=None):
    '''
    '''
    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'user'
    idname = "userid"

    ugroups = []
    if user_groups:
        for ugr in user_groups:
            results = zapi.get_content('usergroup',
                                       'get'
                                       {'search': {'name': name},
                                        'selectUsers': 'userid',
                                        'getRights': 'extend'
                                       })
            if results[0]:
                ugroups.append({'usrgrpid': results[0]['usrgrpid']})

    if not params:
        params = {}

    content = zapi.get_content(zbx_class_name, 
                               'get',
                               {'output': 'extend',
                                'search': {'alias': alias},
                                'selectUsrgrps': ['usrgrpid'],
                               })
    print content
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")
        if not isinstance(params, list) and content['result'][0].has_key(idname):
            params = [content['result'][0][idname]]

        content = zapi.get_content(zbx_class_name, 'delete', params)
        module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':
        params['alias'] = alias
        params['passwd'] = passwd
        params['usrgrps'] = ugroups

        if not exists(content):
            # if we didn't find it, create it
            content = zapi.get_content(zbx_class_name, 'create', params)
            module.exit_json(changed=True, results=content['result'], state='present')
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
            module.exit_json(changed=False, results=zab_results, state="present")

        # We have differences and need to update
        differences[idname] = zab_results[idname]
        content = zapi.get_content(zbx_class_name, 'update', differences)
        module.exit_json(changed=True, results=content['result'], state="present")
    return (False, 'ERROR', 'UNKOWN state')

def usergroup(self, name, rights=None, users=None, state='present', params=None):
    '''
    '''
    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'usergroup'
    idname = "usrgrpid"

    # Fetch groups by name
    perms = []
    if rights:
        for hstgrp, perm in rights:
            results = self.get_content('hostgroup', 'get', {'search': {'name': hstgrp}})
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
            results = self.get_content(zbx_class_name, 'get', {'search': {'name': hstgrp}})
            changed, results, _ = self.user(user, state='list')
            if results[0]:
                userids.append(results[0]['userid'])

    if not params:
        params = {}

    content = zapi.get_content(zbx_class_name, 
                               'get', 
                               {'search': {'name': name},
                                'selectUsers': 'userid',
                               })
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")
        if not isinstance(params, list) and content['result'][0].has_key(idname):
            params = [content['result'][0][idname]]

        content = zapi.get_content(zbx_class_name, 'delete', params)
        module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':
        params['name'] = name
        params['rights'] = perms
        params['userids'] = userids

        if not exists(content):
            # if we didn't find it, create it
            content = zapi.get_content(zbx_class_name, 'create', params)
            module.exit_json(changed=True, results=content['result'], state='present')
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
            module.exit_json(changed=False, results=zab_results, state="present")

        # We have differences and need to update
        differences[idname] = zab_results[idname]
        content = zapi.get_content(zbx_class_name, 'update', differences)
        module.exit_json(changed=True, results=content['result'], state="present")
    return (False, 'ERROR', 'UNKOWN state')

def hostgroup(self, name, state='present', params=None):
    '''
    '''
    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'hostgroup'
    idname = "groupid"

    if not params:
        params = {}

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'search': {'name': name},
                               })
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")
        if not isinstance(params, list) and content['result'][0].has_key(idname):
            params = [content['result'][0][idname]]

        content = zapi.get_content(zbx_class_name, 'delete', params)
        module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':
        params['name'] = name

        if not exists(content):
            # if we didn't find it, create it
            content = zapi.get_content(zbx_class_name, 'create', params)
            module.exit_json(changed=True, results=content['result'], state='present')
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
            module.exit_json(changed=False, results=zab_results, state="present")

        # We have differences and need to update
        differences[idname] = zab_results[idname]
        content = zapi.get_content(zbx_class_name, 'update', differences)
        module.exit_json(changed=True, results=content['result'], state="present")
    return (False, 'ERROR', 'UNKOWN state')

def host(self, name, host_groups=None, templates=None, interfaces=None, state='present', params=None):
    '''
    '''
    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'host'
    idname = "hostid"

    # Fetch groups by name
    groups = []
    if host_groups:
        for hgr in host_groups:
            results = self.get_content('hostgroup', 'get', {'search': {'name': hgr}})
            if results[0]:
                groups.append({'groupid': results[0]['groupid']})

    templs = []
    # Fetch templates by name
    if templates:
        for template_name in templates:
            results = self.get_content('template', 'get', {'search': {'host': template_name}})
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

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'search': {'host': name},
                               'selectGroups': 'groupid',
                               'selectParentTemplates': 'templateid',
                               })
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")
        if not isinstance(params, list) and content['result'][0].has_key(idname):
            params = [content['result'][0][idname]]

        content = zapi.get_content(zbx_class_name, 'delete', params)
        module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':
        params['host'] = name
        params['groups'] = groups
        params['templates'] = templs
        params['interfaces'] = interfaces

        if not exists(content):
            # if we didn't find it, create it
            content = zapi.get_content(zbx_class_name, 'create', params)
            module.exit_json(changed=True, results=content['result'], state='present')
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
            module.exit_json(changed=False, results=zab_results, state="present")

        # We have differences and need to update
        differences[idname] = zab_results[idname]
        content = zapi.get_content(zbx_class_name, 'update', differences)
        module.exit_json(changed=True, results=content['result'], state="present")
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
    zbx_class_name = self.zapi.__getattribute__('trigger')
    zbx_class_name = 'trigger'
    idname = "triggerid"

    # need to look up dependencies by expression? description?
    # TODO
    deps = []
    if dependencies:
        for description in dependencies:
            results = self.get_content('trigger', 
                                       'get', 
                                       {'search': {'description': description},
                                        'expandExpression': True,
                                        'selectDependencies': 'triggerid',
                                       })
            if results[0]:
                deps.append({'triggerid': results[0]['triggerid']})

    if not params:
        params = {}

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'search': {'description': desc},
                               'expandExpression': True,
                               'selectDependencies': 'triggerid',
                               })
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")
        if not isinstance(params, list) and content['result'][0].has_key(idname):
            params = [content['result'][0][idname]]

        content = zapi.get_content(zbx_class_name, 'delete', params)
        module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':
        params['description'] = desc
        params['expression'] = expression
        params['dependencies'] =  deps

        if not exists(content):
            # if we didn't find it, create it
            content = zapi.get_content(zbx_class_name, 'create', params)
            module.exit_json(changed=True, results=content['result'], state='present')
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
            module.exit_json(changed=False, results=zab_results, state="present")

        # We have differences and need to update
        differences[idname] = zab_results[idname]
        content = zapi.get_content(zbx_class_name, 'update', differences)
        module.exit_json(changed=True, results=content['result'], state="present")

    return (False, 'ERROR', 'UNKOWN state')

def item(self, name, key, template_name, zabbix_type=2, vtype='int', interfaceid=None, \
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
    zbx_class_name = 'item'
    idname = "itemid"

    results = self.get_content('template', 'get', {'search': {'host': template_name}})
    templateid = None
    if results:
        templateid = results[0]['templateid']
    else:
        module.exit_json(changed=False, results='Error: Could find template with name %s for item.' % template_name, state="Unkown")

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

    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'search': {'key_': key},
                                'selectApplications': 'applicationid',
                               })
    if state == 'list':
        module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content):
            module.exit_json(changed=False, state="absent")
        if not isinstance(params, list) and content['result'][0].has_key(idname):
            params = [content['result'][0][idname]]

        content = zapi.get_content(zbx_class_name, 'delete', params)
        module.exit_json(changed=True, results=content['result'], state="absent")

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
            content = zapi.get_content(zbx_class_name, 'create', params)
            module.exit_json(changed=True, results=content['result'], state='present')
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
            module.exit_json(changed=False, results=zab_results, state="present")

        # We have differences and need to update
        differences[idname] = zab_results[idname]
        content = zapi.get_content(zbx_class_name, 'update', differences)
        module.exit_json(changed=True, results=content['result'], state="present")
    return (False, 'ERROR', 'UNKOWN state')

def template(self, name, state='present', params=None):
    #Set the instance and the template for the rest of the calls
    zbx_class_name = 'template'
    idname = 'templateid'

    if not params:
        params = {}
    # get a template, see if it exists
    content = zapi.get_content(zbx_class_name,
                               'get',
                               {'search': {'host': name},
                                'selectParentTemplates': 'templateid',
                                'selectGroups': 'groupid',
                               #'selectApplications': extend,
                               })
    if state == 'list':
        return module.exit_json(changed=False, results=content['result'], state="list")

    if state == 'absent':
        if not exists(content):
            return module.exit_json(changed=False, state="absent")
        if not isinstance(params, list) and content['result'][0].has_key(idname):
            params = [content['result'][0][idname]]

        content = zapi.get_content(zbx_class_name, 'delete', params)
        return module.exit_json(changed=True, results=content['result'], state="absent")

    if state == 'present':
        if not exists(content):
            # if we didn't find it, create it
            groups = params.get('groups', [])
            params['groups'] = groups
            params['groups'].append({'groupid': 1})
            params['host'] = name
            params['output'] = 'extend'
            content = zapi.get_content(zbx_class_name, 'create', params)
            return module.exit_json(changed=True, results=content['result'], state='present')
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
            return module.exit_json(changed=False, results=content['result'], state="present")

        # We have differences and need to update
        differences[idname] = zab_results[idname]
        content = zapi.get_content(zbx_class_name, 'update', differences)
        return module.exit_json(changed=True, results=content['result'], state="present")
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
