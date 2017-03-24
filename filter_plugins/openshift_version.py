#!/usr/bin/python

# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4
"""
Custom version comparison filters for use in openshift-ansible
"""

# pylint can't locate distutils.version within virtualenv
# https://github.com/PyCQA/pylint/issues/73
# pylint: disable=no-name-in-module, import-error
from distutils.version import LooseVersion


def gte_function_builder(name, versions):
    """
    Build and return a version comparison function.

    Ex: name = 'oo_version_gte_3_1_or_1_1'
        versions = {'enterprise': '3.1', 'origin': '1.1'}

        returns oo_version_gte_3_1_or_1_1, a function which based on the
        version and deployment type will return true if the provided
        version is greater than or equal to the function's version
    """
    enterprise_version = versions['enterprise']
    origin_version = versions['origin']

    def _gte_function(version, deployment_type):
        """
        Dynamic function created by gte_function_builder.

        Ex: version = '3.1'
            deployment_type = 'openshift-enterprise'
            returns True/False
        """
        version_gte = False
        if 'enterprise' in deployment_type:
            if str(version) >= LooseVersion(enterprise_version):
                version_gte = True
        elif 'origin' in deployment_type:
            if str(version) >= LooseVersion(origin_version):
                version_gte = True
        return version_gte
    _gte_function.__name__ = name
    return _gte_function


# pylint: disable=too-few-public-methods
class FilterModule(object):
    """
    Filters for version checking.
    """
    #: The major versions to start incrementing. (enterprise, origin)
    majors = [(3, 1)]

    #: The minor version to start incrementing
    minor = 3
    #: The number of iterations to increment
    minor_iterations = 10

    def __init__(self):
        """
        Creates a new FilterModule for ose version checking.
        """
        self._filters = {}
        # For each major version
        for enterprise, origin in self.majors:
            # For each minor version in the range
            for minor in range(self.minor, self.minor_iterations):
                # Create the function name
                func_name = 'oo_version_gte_{}_{}_or_{}_{}'.format(
                    enterprise, minor, origin, minor)
                # Create the function with the builder
                func = gte_function_builder(
                    func_name, {
                        'enterprise': '{}.{}.0'.format(enterprise, minor),
                        'origin': '{}.{}.0'.format(origin, minor)
                    })
                # Add the function to the mapping
                self._filters[func_name] = func

        # Create filters with special versioning requirements
        self._filters['oo_version_gte_3_1_or_1_1'] = gte_function_builder('oo_version_gte_3_1_or_1_1',
                                                                          {'enterprise': '3.0.2.905',
                                                                           'origin': '1.1.0'})
        self._filters['oo_version_gte_3_1_1_or_1_1_1'] = gte_function_builder('oo_version_gte_3_1_or_1_1',
                                                                              {'enterprise': '3.1.1',
                                                                               'origin': '1.1.1'})
        self._filters['oo_version_gte_3_2_or_1_2'] = gte_function_builder('oo_version_gte_3_2_or_1_2',
                                                                          {'enterprise': '3.1.1.901',
                                                                           'origin': '1.2.0'})

    def filters(self):
        """
        Return the filters mapping.
        """
        return self._filters
