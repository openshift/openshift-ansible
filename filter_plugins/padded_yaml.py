#
# This filter allows you to expand vars into 
#   multi line yaml snippets 
#   the first line is positioned with in the template
#   the following lines are padded to level * indent spaces
#  
# author Lutz Lange <llange@redhat.com>
# 
# example filter " ... | to_padded_yaml( level=2 )
# ToDo : - test with more complex structures. 
#        - test indentitation feature ( level=2, indent=4 )
#

import yaml
from ansible.utils.unicode import to_unicode

def to_padded_yaml(*a, **kw):
  ''' pad all the yaml content with level spaces exempt the first line '''
  # remove level from **kw if it exsists
  level = 0
  indent = 2
  if kw.has_key('level'):
    level = kw['level']
    kw.pop('level')
  if kw.has_key('indent'):
    indent = kw.pop('indent')
  transformed = yaml.safe_dump(*a, indent=indent, allow_unicode=True, default_flow_style=False, **kw)
  # first line without padding to allow for correct indent of first line
  padded = transformed.split('\n', 1)[0]
  # pad all following lines
  for line in filter(None, transformed.split('\n')[1:]):
    padded += "\n" + " " * level * indent + line
  return to_unicode(padded)

class FilterModule(object):
  ''' Additional yaml Filter to expand multi line yaml snippets '''

  def filters(self):
    return {
      # extra nice yaml
      'to_padded_yaml': to_padded_yaml,
    }


