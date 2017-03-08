'''
 Openshift Logging class that provides useful filters used in Logging
'''

import random


def random_word(source_alpha, length):
    ''' Returns a random word given the source of characters to pick from and resulting length '''
    return ''.join(random.choice(source_alpha) for i in range(length))


def entry_from_named_pair(register_pairs, key):
    ''' Returns the entry in key given results provided by register_pairs '''
    results = register_pairs.get("results")
    if results is None:
        raise RuntimeError("The dict argument does not have a 'results' entry. "
                           "Must not have been created using 'register' in a loop")
    for result in results:
        item = result.get("item")
        if item is not None:
            name = item.get("name")
            if name == key:
                return result["content"]
    raise RuntimeError("There was no entry found in the dict that had an item with a name that matched {}".format(key))


def map_from_pairs(source, delim="="):
    ''' Returns a dict given the source and delim delimited '''
    if source == '':
        return dict()

    return dict(source.split(delim) for item in source.split(","))


# pylint: disable=too-few-public-methods
class FilterModule(object):
    ''' OpenShift Logging Filters '''

    # pylint: disable=no-self-use, too-few-public-methods
    def filters(self):
        ''' Returns the names of the filters provided by this class '''
        return {
            'random_word': random_word,
            'entry_from_named_pair': entry_from_named_pair,
            'map_from_pairs': map_from_pairs,
        }
