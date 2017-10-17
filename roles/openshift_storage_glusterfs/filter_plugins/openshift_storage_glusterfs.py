'''
 Openshift Storage GlusterFS class that provides useful filters used in GlusterFS
'''


def map_from_pairs(source, delim="="):
    ''' Returns a dict given the source and delim delimited '''
    if source == '':
        return dict()

    return dict(item.split(delim) for item in source.split(","))


# pylint: disable=too-few-public-methods
class FilterModule(object):
    ''' OpenShift Storage GlusterFS Filters '''

    # pylint: disable=no-self-use, too-few-public-methods
    def filters(self):
        ''' Returns the names of the filters provided by this class '''
        return {
            'map_from_pairs': map_from_pairs
        }
