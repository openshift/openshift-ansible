#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Custom filters for use with openshift named certificates
'''


class FilterModule(object):
    ''' Custom ansible filters for use with openshift named certificates'''

    @staticmethod
    def oo_named_certificates_list(named_certificates):
        ''' Returns named certificates list with correct fields for the master
            config file.'''
        return [{'certFile': named_certificate['certfile'],
                 'keyFile': named_certificate['keyfile'],
                 'names': named_certificate['names']} for named_certificate in named_certificates]

    def filters(self):
        ''' returns a mapping of filters to methods '''
        return {"oo_named_certificates_list": self.oo_named_certificates_list}
