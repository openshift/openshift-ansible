'''
 Openshift Logging class that provides useful filters used in Logging.

 This should be removed after map_from_pairs is no longer used in __deprecations_logging.yml
'''


def map_from_pairs(source, delim="="):
    ''' Returns a dict given the source and delim delimited '''
    if source == '':
        return dict()

    return dict(item.split(delim) for item in source.split(","))


# pylint: disable=too-few-public-methods
class FilterModule(object):
    ''' OpenShift Logging Filters '''

    # pylint: disable=no-self-use, too-few-public-methods
    def filters(self):
        ''' Returns the names of the filters provided by this class '''
        return {
            'map_from_pairs': map_from_pairs
        }
