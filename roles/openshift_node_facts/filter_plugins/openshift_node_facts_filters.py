#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Custom filters for use in openshift-node
'''
from ansible import errors


class FilterModule(object):
    ''' Custom ansible filters for use by openshift_node_facts role'''

    @staticmethod
    def node_get_dns_ip(openshift_dns_ip, hostvars):
        ''' Navigates the complicated logic of when to set dnsIP

            In all situations if they've set openshift_dns_ip use that
            For 1.0/3.0 installs we use the openshift_master_cluster_vip, openshift_node_first_master_ip, else None
            For 1.1/3.1 installs we use openshift_master_cluster_vip, else None (product will use kube svc ip)
            For 1.2/3.2+ installs we set to the node's default interface ip
        '''

        if not issubclass(type(hostvars), dict):
            raise errors.AnsibleFilterError("|failed expects hostvars is a dict")

        # We always use what they've specified if they've specified a value
        if openshift_dns_ip is not None:
            return openshift_dns_ip
        return hostvars['ansible_default_ipv4']['address']

    def filters(self):
        ''' returns a mapping of filters to methods '''
        return {'node_get_dns_ip': self.node_get_dns_ip}
