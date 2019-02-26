#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=too-many-lines
"""
Custom filters for use in openshift-ansible
"""
import ast

from collections import Mapping
from ansible import errors

# pylint: disable=import-error,no-name-in-module
from ansible.module_utils.six import string_types


# pylint: disable=C0103

def lib_utils_oo_select_keys(data, keys):
    """ This returns a list, which contains the value portions for the keys
        Ex: data = { 'a':1, 'b':2, 'c':3 }
            keys = ['a', 'c']
            returns [1, 3]
    """

    if not isinstance(data, Mapping):
        raise errors.AnsibleFilterError("|lib_utils_oo_select_keys failed expects to filter on a dict or object")

    if not isinstance(keys, list):
        raise errors.AnsibleFilterError("|lib_utils_oo_select_keys failed expects first param is a list")

    # Gather up the values for the list of keys passed in
    retval = [data[key] for key in keys if key in data]

    return retval


def lib_utils_oo_dict_to_keqv_list(data):
    """Take a dict and return a list of k=v pairs

        Input data:
        {'a': 1, 'b': 2}

        Return data:
        ['a=1', 'b=2']
    """
    if not isinstance(data, dict):
        try:
            # This will attempt to convert something that looks like a string
            # representation of a dictionary (including json) into a dictionary.
            data = ast.literal_eval(data)
        except ValueError:
            msg = "|failed expects first param is a dict. Got {}. Type: {}"
            msg = msg.format(str(data), str(type(data)))
            raise errors.AnsibleFilterError(msg)
    return ['='.join(str(e) for e in x) for x in data.items()]


def lib_utils_oo_image_tag_to_rpm_version(version, include_dash=False):
    """ Convert an image tag string to an RPM version if necessary
        Empty strings and strings that are already in rpm version format
        are ignored. Also remove non semantic version components.

        Ex. v3.2.0.10 -> -3.2.0.10
            v1.2.0-rc1 -> -1.2.0
    """
    if not isinstance(version, string_types):
        raise errors.AnsibleFilterError("|failed expects a string or unicode")
    if version.startswith("v"):
        version = version[1:]
        # Strip release from requested version, we no longer support this.
        version = version.split('-')[0]

    if include_dash and version and not version.startswith("-"):
        version = "-" + version

    return version


class FilterModule(object):
    """ Custom ansible filter mapping """

    # pylint: disable=no-self-use, too-few-public-methods
    def filters(self):
        """ returns a mapping of filters to methods """
        return {
            "lib_utils_oo_select_keys": lib_utils_oo_select_keys,
            "lib_utils_oo_dict_to_keqv_list": lib_utils_oo_dict_to_keqv_list,
            "lib_utils_oo_image_tag_to_rpm_version": lib_utils_oo_image_tag_to_rpm_version,
        }
