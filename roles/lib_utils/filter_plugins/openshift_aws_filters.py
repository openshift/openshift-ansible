#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Custom filters for use in openshift_aws
'''

from ansible import errors


class FilterModule(object):
    ''' Custom ansible filters for use by openshift_aws role'''

    @staticmethod
    def scale_groups_serial(scale_group_info, upgrade=False):
        ''' This function will determine what the deployment serial should be and return it

          Search through the tags and find the deployment_serial tag. Once found,
          determine if an increment is needed during an upgrade.
          if upgrade is true then increment the serial and return it
          else return the serial
        '''
        if scale_group_info == []:
            return 1

        scale_group_info = scale_group_info[0]

        if not isinstance(scale_group_info, dict):
            raise errors.AnsibleFilterError("|filter plugin failed: Expected scale_group_info to be a dict")

        serial = None

        for tag in scale_group_info['tags']:
            if tag['key'] == 'deployment_serial':
                serial = int(tag['value'])
                if upgrade:
                    serial += 1
                break
        else:
            raise errors.AnsibleFilterError("|filter plugin failed: deployment_serial tag was not found")

        return serial

    @staticmethod
    def scale_groups_match_capacity(scale_group_info):
        ''' This function will verify that the scale group instance count matches
            the scale group desired capacity

        '''
        for scale_group in scale_group_info:
            if scale_group['desired_capacity'] != len(scale_group['instances']):
                return False

        return True

    @staticmethod
    def build_instance_tags(clusterid):
        ''' This function will return a dictionary of the instance tags.

            The main desire to have this inside of a filter_plugin is that we
            need to build the following key.

            {"kubernetes.io/cluster/{{ openshift_aws_clusterid }}": "{{ openshift_aws_clusterid}}"}

        '''
        tags = {'clusterid': clusterid,
                'kubernetes.io/cluster/{}'.format(clusterid): clusterid}

        return tags

    def filters(self):
        ''' returns a mapping of filters to methods '''
        return {'build_instance_tags': self.build_instance_tags,
                'scale_groups_match_capacity': self.scale_groups_match_capacity,
                'scale_groups_serial': self.scale_groups_serial}
