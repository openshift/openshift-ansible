'''
 Openshift Sanitize inventory class that provides useful filters used in Logging.
'''


import re


# This should be removed after map_from_pairs is no longer used in __deprecations_logging.yml
def map_from_pairs(source, delim="="):
    ''' Returns a dict given the source and delim delimited '''
    if source == '':
        return dict()

    return dict(item.split(delim) for item in source.split(","))


def vars_with_pattern(source, pattern=""):
    ''' Returns a list of variables whose name matches the given pattern '''
    if source == '':
        return list()

    var_list = list()

    var_pattern = re.compile(pattern)

    for item in source:
        if var_pattern.match(item):
            var_list.append(item)

    return var_list


# pylint: disable=too-few-public-methods
class FilterModule(object):
    ''' OpenShift Logging Filters '''

    # pylint: disable=no-self-use, too-few-public-methods
    def filters(self):
        ''' Returns the names of the filters provided by this class '''
        return {
            'map_from_pairs': map_from_pairs,
            'vars_with_pattern': vars_with_pattern
        }
