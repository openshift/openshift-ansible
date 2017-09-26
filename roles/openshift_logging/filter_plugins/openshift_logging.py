'''
 Openshift Logging class that provides useful filters used in Logging
'''

import random


def es_storage(os_logging_facts, dc_name, pvc_claim, root='elasticsearch'):
    '''Return a hash with the desired storage for the given ES instance'''
    deploy_config = os_logging_facts[root]['deploymentconfigs'].get(dc_name)
    if deploy_config:
        storage = deploy_config['volumes']['elasticsearch-storage']
        if storage.get('hostPath'):
            return dict(kind='hostpath', path=storage.get('hostPath').get('path'))
    if len(pvc_claim.strip()) > 0:
        return dict(kind='pvc', pvc_claim=pvc_claim)
    return dict(kind='emptydir')


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

    return dict(item.split(delim) for item in source.split(","))


def serviceaccount_name(qualified_sa):
    ''' Returns the simple name from a fully qualified name '''
    return qualified_sa.split(":")[-1]


def serviceaccount_namespace(qualified_sa, default=None):
    ''' Returns the namespace from a fully qualified name '''
    seg = qualified_sa.split(":")
    if len(seg) > 1:
        return seg[-2]
    if default:
        return default
    return seg[-1]


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
            'es_storage': es_storage,
            'serviceaccount_name': serviceaccount_name,
            'serviceaccount_namespace': serviceaccount_namespace
        }
