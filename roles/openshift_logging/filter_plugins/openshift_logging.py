import random, string
import shutil
import sys
import StringIO

def random_word(source_alpha,length):
    return ''.join(random.choice(source_alpha) for i in range(length))

def entry_from_named_pair(register_pairs, key):
    from ansible.utils.display import Display
    results = register_pairs.get("results")
    if results == None:
        raise RuntimeError("The dict argument does not have a 'results' entry.  Must not have been created using 'register' in a loop")
    for result in results:
        item = result.get("item")
        if item != None:
            name = item.get("name") 
            if name == key:
                return result["content"]
    raise RuntimeError("There was no entry found in the dict that had an item with a name that matched {}".format(key))

class FilterModule(object):
    ''' OpenShift Logging Filters '''

    def filters(self):
        return {
            'random_word': random_word,
            'entry_from_named_pair': entry_from_named_pair,
        }
