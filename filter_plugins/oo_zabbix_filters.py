#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4
'''
Custom zabbix filters for use in openshift-ansible
'''

import pdb

class FilterModule(object):
    ''' Custom zabbix ansible filters '''

    @staticmethod
    def create_data(data, results, key, new_key):
        '''Take a dict, filter through results and add results['key'] to dict
        '''
        new_list = [app[key] for app in results]
        data[new_key] = new_list
        return data

    @staticmethod
    def oo_set_zbx_trigger_triggerid(item, trigger_results):
        '''Set zabbix trigger id from trigger results
        '''
        if isinstance(trigger_results, list):
            item['triggerid'] = trigger_results[0]['triggerid']
            return item

        item['triggerid'] = trigger_results['triggerids'][0]
        return item

    @staticmethod
    def oo_set_zbx_item_hostid(item, template_results):
        ''' Set zabbix host id from template results
        '''
        if isinstance(template_results, list):
            item['hostid'] = template_results[0]['templateid']
            return item

        item['hostid'] = template_results['templateids'][0]
        return item

    @staticmethod
    def oo_pdb(arg):
        ''' This pops you into a pdb instance where arg is the data passed in
            from the filter.
            Ex: "{{ hostvars | oo_pdb }}"
        '''
        pdb.set_trace()
        return arg

    @staticmethod
    def select_by_name(ans_data, data):
        ''' test
        '''
        for zabbix_item in data:
            if ans_data['name'] == zabbix_item:
                data[zabbix_item]['params']['hostid'] = ans_data['templateid']
                return data[zabbix_item]['params']
        return None

    @staticmethod
    def oo_build_zabbix_collect(data, string, value):
        ''' Build a list of dicts from a list of data matched on string attribute
        '''
        rval = []
        for item in data:
            if item[string] == value:
                rval.append(item)

        return rval

    @staticmethod
    def oo_build_zabbix_list_dict(values, string):
        ''' Build a list of dicts with string as key for each value
        '''
        rval = []
        for value in values:
            rval.append({string: value})
        return rval

    @staticmethod
    def oo_remove_attr_from_list_dict(data, attr):
        ''' Remove a specific attribute from a dict
        '''
        attrs = []
        if isinstance(attr, str):
            attrs.append(attr)
        else:
            attrs = attr

        for attribute in attrs:
            for _entry in data:
                _entry.pop(attribute, None)

        return data

    @staticmethod
    def itservice_results_builder(data, clusters, keys):
        '''Take a list of dict results,
           loop through each results and create a hash
           of:
             [{clusterid:  cluster1, key: 111 }]
        '''
        r_list = []
        for cluster in clusters:
            for results in data:
                if cluster == results['item'][0]:
                    results = results['results']
                    if results and len(results) > 0 and all([results[0].has_key(_key) for _key in keys]):
                        tmp = {}
                        tmp['clusterid'] = cluster
                        for key in keys:
                            tmp[key] = results[0][key]
                        r_list.append(tmp)

        return r_list

    @staticmethod
    def itservice_dependency_builder(data, cluster):
        '''Take a list of dict results,
           loop through each results and create a hash
           of:
             [{clusterid:  cluster1, key: 111 }]
        '''
        r_list = []
        for dep in data:
            if cluster == dep['clusterid']:
                r_list.append({'name': '%s - %s' % (dep['clusterid'], dep['description']), 'dep_type': 'hard'})

        return r_list

    @staticmethod
    def itservice_dep_builder_list(data):
        '''Take a list of dict results,
           loop through each results and create a hash
           of:
             [{clusterid:  cluster1, key: 111 }]
        '''
        r_list = []
        for dep in data:
            r_list.append({'name': '%s' % dep, 'dep_type': 'hard'})

        return r_list

    def filters(self):
        ''' returns a mapping of filters to methods '''
        return {
            "select_by_name": self.select_by_name,
            "oo_set_zbx_item_hostid": self.oo_set_zbx_item_hostid,
            "oo_set_zbx_trigger_triggerid": self.oo_set_zbx_trigger_triggerid,
            "oo_build_zabbix_list_dict": self.oo_build_zabbix_list_dict,
            "create_data": self.create_data,
            "oo_build_zabbix_collect": self.oo_build_zabbix_collect,
            "oo_remove_attr_from_list_dict": self.oo_remove_attr_from_list_dict,
            "itservice_results_builder": self.itservice_results_builder,
            "itservice_dependency_builder": self.itservice_dependency_builder,
            "itservice_dep_builder_list": self.itservice_dep_builder_list,
        }
