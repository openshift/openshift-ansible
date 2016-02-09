#!/usr/bin/python
#
# (c) 2015, Russell Harrison <rharriso@redhat.com>
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
'''Ansible module to manage records in the Dyn Managed DNS service'''
DOCUMENTATION = '''
---
module: dyn_record
version_added: "1.9"
short_description: Manage records in the Dyn Managed DNS service.
description:
  - "Manages DNS records via the REST API of the Dyn Managed DNS service.  It
  - "handles records only; there is no manipulation of zones or account support"
  - "yet. See: U(https://help.dyn.com/dns-api-knowledge-base/)"
options:
  state:
    description:
      -"Whether the record should be c(present) or c(absent). Optionally the"
      - "state c(list) can be used to return the current value of a record."
    required: true
    choices: [ 'present', 'absent', 'list' ]
    default: present

  customer_name:
    description:
      - "The Dyn customer name for your account.  If not set the value of the"
      - "c(DYNECT_CUSTOMER_NAME) environment variable is used."
    required: false
    default: nil

  user_name:
    description:
      - "The Dyn user name to log in with. If not set the value of the"
      - "c(DYNECT_USER_NAME) environment variable is used."
    required: false
    default: null

  user_password:
    description:
      - "The Dyn user's password to log in with. If not set the value of the"
      - "c(DYNECT_PASSWORD) environment variable is used."
    required: false
    default: null

  zone:
    description:
      - "The DNS zone in which your record is located."
    required: true
    default: null

  record_fqdn:
    description:
      - "Fully qualified domain name of the record name to get, create, delete,"
      - "or update."
    required: true
    default: null

  record_type:
    description:
      - "Record type."
    required: true
    choices: [ 'A', 'AAAA', 'CNAME', 'PTR', 'TXT' ]
    default: null

  record_value:
    description:
      - "Record value. If record_value is not specified; no changes will be"
      - "made and the module will fail"
    required: false
    default: null

  record_ttl:
    description:
      - 'Record's "Time to live".  Number of seconds the record remains cached'
      - 'in DNS servers or c(0) to use the default TTL for the zone.'
    required: false
    default: 0

notes:
  - The module makes a broad assumption that there will be only one record per "node" (FQDN).
  - This module returns record(s) in the "result" element when 'state' is set to 'present'. This value can be be registered and used in your playbooks.

requirements: [ dyn ]
author: "Russell Harrison"
'''

try:
    IMPORT_ERROR = False
    from dyn.tm.session import DynectSession
    from dyn.tm.zones import Zone
    import dyn.tm.errors
    import os

except ImportError as error:
    IMPORT_ERROR = str(error)

# Each of the record types use a different method for the value.
RECORD_PARAMS = {
    'A'     : {'value_param': 'address'},
    'AAAA'  : {'value_param': 'address'},
    'CNAME' : {'value_param': 'cname'},
    'PTR'   : {'value_param': 'ptrdname'},
    'TXT'   : {'value_param': 'txtdata'}
}

# You'll notice that the value_param doesn't match the key (records_key)
# in the dict returned from Dyn when doing a dyn_node.get_all_records()
# This is a frustrating lookup dict to allow mapping to the RECORD_PARAMS
# dict so we can lookup other values in it efficiently

def get_record_type(record_key):
    '''Get the record type represented by the keys returned from get_any_records.'''
    return record_key.replace('_records', '').upper()

def get_record_key(record_type):
    '''Get the key to look up records in the dictionary returned from get_any_records.'''
    return record_type.lower() + '_records'

def get_any_records(module, node):
    '''Get any records for a given node'''
    # Lets get a list of the A records for the node
    try:
        records = node.get_any_records()
    except dyn.tm.errors.DynectGetError as error:
        if 'Not in zone' in str(error):
            # The node isn't in the zone so we'll return an empty dictionary
            return {}
        else:
            # An unknown error happened so we'll need to return it.
            module.fail_json(msg='Unable to get records',
                             error=str(error))

    # Return a dictionary of the record objects
    return records

def get_record_values(records):
    '''Get the record values for each record returned by get_any_records.'''
    # This simply returns the values from a dictionary of record objects
    ret_dict = {}
    for key in records.keys():
        record_type = get_record_type(key)
        record_value_param = RECORD_PARAMS[record_type]['value_param']
        ret_dict[key] = [getattr(elem, record_value_param) for elem in records[key]]
    return ret_dict

def main():
    '''Ansible module for managing Dyn DNS records.'''
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(required=True, choices=['present', 'absent', 'list']),
            customer_name=dict(default=os.environ.get('DYNECT_CUSTOMER_NAME', None), type='str'),
            user_name=dict(default=os.environ.get('DYNECT_USER_NAME', None), type='str', no_log=True),
            user_password=dict(default=os.environ.get('DYNECT_PASSWORD', None), type='str', no_log=True),
            zone=dict(required=True),
            record_fqdn=dict(required=False),
            record_type=dict(required=False, choices=[
                'A', 'AAAA', 'CNAME', 'PTR', 'TXT']),
            record_value=dict(required=False),
            record_ttl=dict(required=False, default=0, type='int'),
        ),
        required_together=(
            ['record_fqdn', 'record_value', 'record_ttl', 'record_type']
        )
    )

    if IMPORT_ERROR:
        module.fail_json(msg="Unable to import dyn module: https://pypi.python.org/pypi/dyn",
                         error=IMPORT_ERROR)

    # Start the Dyn session
    try:
        _ = DynectSession(module.params['customer_name'],
                          module.params['user_name'],
                          module.params['user_password'])
    except dyn.tm.errors.DynectAuthError as error:
        module.fail_json(msg='Unable to authenticate with Dyn',
                         error=str(error))

    # Retrieve zone object
    try:
        dyn_zone = Zone(module.params['zone'])
    except dyn.tm.errors.DynectGetError as error:
        if 'No such zone' in str(error):
            module.fail_json(
                msg="Not a valid zone for this account",
                zone=module.params['zone']
            )
        else:
            module.fail_json(msg="Unable to retrieve zone",
                             error=str(error))


    # To retrieve the node object we need to remove the zone name from the FQDN
    dyn_node_name = module.params['record_fqdn'].replace('.' + module.params['zone'], '')

    # Retrieve the zone object from dyn
    dyn_zone = Zone(module.params['zone'])

    # Retrieve the node object from dyn
    dyn_node = dyn_zone.get_node(node=dyn_node_name)

    # All states will need a list of the exiting records for the zone.
    dyn_node_records = get_any_records(module, dyn_node)

    if module.params['state'] == 'list':
        module.exit_json(changed=False,
                         records=get_record_values(
                             dyn_node_records,
                         ))

    if module.params['state'] == 'present':

        # First get a list of existing records for the node
        values = get_record_values(dyn_node_records)
        value_key = get_record_key(module.params['record_type'])

        # Check to see if the record is already in place before doing anything.
        if (dyn_node_records and
                dyn_node_records[value_key][0].ttl == module.params['record_ttl'] and
                module.params['record_value'] in values[value_key]):

            module.exit_json(changed=False)


        # Working on the assumption that there is only one record per
        # node we will first delete the node if there are any records before
        # creating the correct record
        if dyn_node_records:
            dyn_node.delete()

        # Now lets create the correct node entry.
        dyn_zone.add_record(dyn_node_name,
                            module.params['record_type'],
                            module.params['record_value'],
                            module.params['record_ttl']
                           )

        # Now publish the zone since we've updated it.
        dyn_zone.publish()
        module.exit_json(changed=True,
                         msg="Created node %s in zone %s" % (dyn_node_name, module.params['zone']))

    if module.params['state'] == 'absent':
        # If there are any records present we'll want to delete the node.
        if dyn_node_records:
            dyn_node.delete()
            # Publish the zone since we've modified it.
            dyn_zone.publish()
            module.exit_json(changed=True,
                             msg="Removed node %s from zone %s" % (dyn_node_name, module.params['zone']))
        else:
            module.exit_json(changed=False)

# Ansible tends to need a wild card import so we'll use it here
# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import, locally-disabled
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
