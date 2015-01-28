from ansible import errors, runner
import json
import pdb

def oo_pdb(arg):
  ''' This pops you into a pdb instance where arg is the data passed in from the filter.
        Ex: "{{ hostvars | oo_pdb }}"
  '''
  pdb.set_trace()
  return arg

def oo_len(arg):
  ''' This returns the length of the argument
        Ex: "{{ hostvars | oo_len }}"
  '''
  return len(arg)

def get_attr(data, attribute=None):
  ''' This looks up dictionary attributes of the form a.b.c and returns the value.
        Ex: data = {'a': {'b': {'c': 5}}}
            attribute = "a.b.c"
            returns 5
  '''

  if not attribute:
    raise errors.AnsibleFilterError("|failed expects attribute to be set")

  ptr = data
  for attr in attribute.split('.'):
    ptr = ptr[attr]

  return ptr

def oo_collect(data, attribute=None):
  ''' This takes a list of dict and collects all attributes specified into a list
        Ex: data = [ {'a':1,'b':5}, {'a':2}, {'a':3} ]
            attribute = 'a'
            returns [1, 2, 3]
  '''

  if not issubclass(type(data), list):
    raise errors.AnsibleFilterError("|failed expects to filter on a List")

  if not attribute:
    raise errors.AnsibleFilterError("|failed expects attribute to be set")

  retval = [get_attr(d, attribute) for d in data]

  return retval

def oo_select_keys(data, keys):
  ''' This returns a list, which contains the value portions for the keys
        Ex: data = { 'a':1, 'b':2, 'c':3 }
            keys = ['a', 'c']
            returns [1, 3]
  '''

  if not issubclass(type(data), dict):
    raise errors.AnsibleFilterError("|failed expects to filter on a Dictionary")

  if not issubclass(type(keys), list):
    raise errors.AnsibleFilterError("|failed expects first param is a list")

  # Gather up the values for the list of keys passed in
  retval = [data[key] for key in keys]

  return retval

def oo_max_nb_minions(groupname, groups, hostvars):
  ''' This computes the max of the 'nb_minions' fact of the machines
        of the given groupname
  '''
  if groupname not in groups:
    return 0

  m = 0
  for host in groups[groupname]:
    if int(hostvars[host]['ansible_local']['minion']['minion']['nb_minions']) > m:
      m = int(hostvars[host]['ansible_local']['minion']['minion']['nb_minions'])
  return m

class FilterModule (object):
  def filters(self):
    return {
      "oo_select_keys": oo_select_keys,
      "oo_collect": oo_collect,
      "oo_len": oo_len,
      "oo_pdb": oo_pdb,
      "oo_max_nb_minions": oo_max_nb_minions
    }
