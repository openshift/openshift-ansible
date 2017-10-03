#!/usr/bin/python
# -*- coding: utf-8 -*-
"""
Custom version comparison filters for use in openshift-ansible
"""

# pylint can't locate distutils.version within virtualenv
# https://github.com/PyCQA/pylint/issues/73
# pylint: disable=no-name-in-module, import-error
from distutils.version import LooseVersion


def legacy_gte_function_builder(name, versions):
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
        if deployment_type == 'openshift-enterprise':
            if str(version) >= LooseVersion(enterprise_version):
                version_gte = True
        else:
            if str(version) >= LooseVersion(origin_version):
                version_gte = True
        return version_gte
    _gte_function.__name__ = name
    return _gte_function


def gte_function_builder(name, gte_version):
    """
    Build and return a version comparison function.

    Ex: name = 'oo_version_gte_3_6'
        version = '3.6'

        returns oo_version_gte_3_6, a function which based on the
        version will return true if the provided version is greater
        than or equal to the function's version
    """
    def _gte_function(version):
        """
        Dynamic function created by gte_function_builder.

        Ex: version = '3.1'
            returns True/False
        """
        version_gte = False
        if str(version) >= LooseVersion(gte_version):
            version_gte = True
        return version_gte
    _gte_function.__name__ = name
    return _gte_function


# pylint: disable=too-few-public-methods
class FilterModule(object):
    """
    Filters for version checking.
    """
    # Each element of versions is composed of (major, minor_start, minor_end)
    # Origin began versioning 3.x with 3.6, so begin 3.x with 3.6.
    versions = [(3, 6, 10)]

    def __init__(self):
        """
        Creates a new FilterModule for ose version checking.
        """
        self._filters = {}

        # For each set of (major, minor, minor_iterations)
        for major, minor_start, minor_end in self.versions:
            # For each minor version in the range
            for minor in range(minor_start, minor_end):
                # Create the function name
                func_name = 'oo_version_gte_{}_{}'.format(major, minor)
                # Create the function with the builder
                func = gte_function_builder(func_name, "{}.{}.0".format(major, minor))
                # Add the function to the mapping
                self._filters[func_name] = func

        # Create filters with special versioning requirements.
        # Treat all Origin 1.x as special case.
        legacy_filters = [{'name': 'oo_version_gte_3_1_or_1_1',
                           'versions': {'enterprise': '3.0.2.905',
                                        'origin': '1.1.0'}},
                          {'name': 'oo_version_gte_3_1_1_or_1_1_1',
                           'versions': {'enterprise': '3.1.1',
                                        'origin': '1.1.1'}},
                          {'name': 'oo_version_gte_3_2_or_1_2',
                           'versions': {'enterprise': '3.1.1.901',
                                        'origin': '1.2.0'}},
                          {'name': 'oo_version_gte_3_3_or_1_3',
                           'versions': {'enterprise': '3.3.0',
                                        'origin': '1.3.0'}},
                          {'name': 'oo_version_gte_3_4_or_1_4',
                           'versions': {'enterprise': '3.4.0',
                                        'origin': '1.4.0'}},
                          {'name': 'oo_version_gte_3_5_or_1_5',
                           'versions': {'enterprise': '3.5.0',
                                        'origin': '1.5.0'}}]
        for legacy_filter in legacy_filters:
            self._filters[legacy_filter['name']] = legacy_gte_function_builder(legacy_filter['name'],
                                                                               legacy_filter['versions'])

    def filters(self):
        """
        Return the filters mapping.
        """
        return self._filters
