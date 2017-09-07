#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Custom filters for use in openshift_aws
'''


class FilterModule(object):
    ''' Custom ansible filters for use by openshift_aws role'''

    @staticmethod
    def build_instance_tags(clusterid, status='owned'):
        ''' This function will return a dictionary of the instance tags.

            The main desire to have this inside of a filter_plugin is that we
            need to build the following key.

            {"kubernetes.io/cluster/{{ openshift_aws_clusterid }}": 'owned'}

        '''
        tags = {'clusterid': clusterid,
                'kubernetes.io/cluster/{}'.format(clusterid): status}

        return tags

    def filters(self):
        ''' returns a mapping of filters to methods '''
        return {'build_instance_tags': self.build_instance_tags}
