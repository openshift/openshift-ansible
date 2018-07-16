#!/usr/bin/env python
#
# vim: expandtab:tabstop=4:shiftwidth=4
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
# pylint: disable=too-many-branches

# -*- coding: utf-8 -*-
""".

module: dyn_record
version_added: '1.9'
short_description: Manage records in the Dyn Managed DNS service.
description:
  - "Manages DNS records via the REST API of the Dyn Managed DNS service.  It
  handles records only; there is no manipulation of zones or account support
  yet.  See: U(https://help.dyn.com/dns-api-knowledge-base/)"
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
      - "Fully qualified domain name of the record name to get, create,
      delete,"
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
      - 'This option is mutually exclusive with use_zone_ttl'
    required: false
    default: 0

  use_zone_ttl:
    description:
      - 'Use the DYN Zone's Default TTL'
      - 'This option is mutually exclusive with record_ttl'
    required: false
    default: false
    mutually exclusive with: record_ttl

notes:
  - The module makes a broad assumption that there will be only one record per
  "node" (FQDN).
  - This module makes an assumptions that record types will not be changed
  (ie. CNAME to AAAA). For this, first delete then create the new record.
  - This module returns record(s) in the "result" element when 'state' is set
  to 'present'. This value can be be registered and used in your playbooks.

requirements: [ dyn ]
author: "Russell Harrison"

"""

EXAMPLES = '''
# Attempting to cname www.example.com to web1.example.com
- name: Update CNAME record
  dyn_record:
    state: present
    record_fqdn: www.example.com
    zone: example.com
    record_type: CNAME
    record_value: web1.example.com
    record_ttl: 7200

# Use the zones default TTL
- name: Update CNAME record
  dyn_record:
    state: present
    record_fqdn: www.example.com
    zone: example.com
    record_type: CNAME
    record_value: web1.example.com
    use_zone_ttl: true

- name: Update A record
  dyn_record:
    state: present
    record_fqdn: web1.example.com
    zone: example.com
    record_value: 10.0.0.10
    record_type: A
'''

try:
    IMPORT_ERROR = False
    # Ansible tends to need a wild card import so we'll use it here
    # pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import,
    # locally-disabled
    from ansible.module_utils.basic import AnsibleModule
    from dyn.tm.session import DynectSession
    from dyn.tm.zones import Zone
    import dyn.tm.errors
    import os

except ImportError as error:
    # pylint: disable=redefined-variable-type
    IMPORT_ERROR = str(error)

# Each of the record types use a different method for the value.
RECORD_PARAMS = {
    'A': {'value_param': 'address'},
    'AAAA': {'value_param': 'address'},
    'CNAME': {'value_param': 'cname'},
    'PTR': {'value_param': 'ptrdname'},
    'TXT': {'value_param': 'txtdata'}
}


# You'll notice that the value_param doesn't match the key (records_key)
# in the dict returned from Dyn when doing a dyn_node.get_all_records()
# This is a frustrating lookup dict to allow mapping to the RECORD_PARAMS
# dict so we can lookup other values in it efficiently

def get_record_type(record_key):
    """Get the record type represented by the keys returned from get_any_records."""
    return record_key.replace('_records', '').upper()


def get_record_key(record_type):
    """Get key to look up records in the dictionary returned from get_any_records."""
    return record_type.lower() + '_records'


def get_any_records(module, node):
    """Get any records for a given node."""
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
    """Get the record values for each record returned by get_any_records."""
    # This simply returns the values from a record
    ret_dict = {}
    for key in records.keys():
        record_type = get_record_type(key)
        params = [RECORD_PARAMS[record_type]['value_param'],
                  'ttl',
                  'zone',
                  'fqdn']
        ret_dict[key] = []
        properties = {}
        for elem in records[key]:
            for param in params:
                properties[param] = getattr(elem, param)
            ret_dict[key].append(properties)

    return ret_dict


def update_record_values(dyn_record, record_type, record_value, ttl):
    """Update record values."""
    rkey = get_record_key(record_type)
    for record in dyn_record[rkey]:
        if record_type == 'CNAME':
            record.cname = record_value
        elif record_type == 'A' or record_type == 'AAAA':
            record.address = record_value
        elif record_type == 'PTR':
            record.ptrdname = record_value
        elif record_type == 'TXT':
            record.txtdata = record_value
        record.ttl = ttl

    # Assuming 1 record only per node
    return dyn_record[rkey][0]


def same_record_types(record_type_key, dyn_values):
    """Check to see if dyn_values includes the same record type."""
    return record_type_key in dyn_values


def compare_record_values(record_type_key, user_record_value, dyn_values):
    """Verify the user record_value exists in dyn."""
    rtype = get_record_type(record_type_key)

    # check to see if the dyn_values include the record type
    if not same_record_types(record_type_key, dyn_values):
        return False

    for record in dyn_values[record_type_key]:
        if RECORD_PARAMS[rtype]['value_param'] in record and \
           user_record_value in record[RECORD_PARAMS[rtype]['value_param']]:
            return True

    return False


def compare_record_ttl(record_type_key,
                       user_record_value,
                       dyn_values,
                       user_param_ttl):
    """Verify the ttls match for the record."""
    rtype = get_record_type(record_type_key)
    for record in dyn_values[record_type_key]:
        # find the right record
        if user_record_value in record[RECORD_PARAMS[rtype]['value_param']]:
            # Compare ttls from the records
            if int(record['ttl']) == user_param_ttl:
                return True

    return False


# pylint: disable=too-many-statements
def main():
    """Ansible module for managing Dyn DNS records."""
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present',
                       choices=['present', 'absent', 'list']),
            customer_name=dict(
                default=os.environ.get('DYNECT_CUSTOMER_NAME', None),
                type='str'),
            user_name=dict(
                default=os.environ.get('DYNECT_USER_NAME', None),
                type='str',
                no_log=True),
            user_password=dict(
                default=os.environ.get('DYNECT_PASSWORD', None),
                type='str',
                no_log=True),
            zone=dict(required=True, type='str'),
            record_fqdn=dict(required=False, type='str'),
            record_type=dict(required=False, type='str', choices=[
                'A', 'AAAA', 'CNAME', 'PTR', 'TXT']),
            record_value=dict(required=False, type='str'),
            record_ttl=dict(required=False, default=None, type='int'),
            use_zone_ttl=dict(required=False, default=False),
        ),
        required_together=(
            ['record_fqdn', 'record_value', 'record_ttl', 'record_type']
        ),
        mutually_exclusive=[('record_ttl', 'use_zone_ttl')]
    )

    if IMPORT_ERROR:
        module.fail_json(
            msg="Unable to import dyn module: \
              https://pypi.python.org/pypi/dyn",
            error=IMPORT_ERROR)

    if module.params['record_ttl'] is not None and \
            int(module.params['record_ttl']) <= 0:
        module.fail_json(msg="Invalid Value for record TTL")

    # Start the Dyn session
    try:
        DynectSession(module.params['customer_name'],
                      module.params['user_name'],
                      module.params['user_password'])
    except dyn.tm.errors.DynectAuthError as error:
        module.fail_json(
            msg='Unable to authenticate with Dyn',
            error=str(error))

    # Retrieve zone object
    try:
        dyn_zone = Zone(module.params['zone'])
    except dyn.tm.errors.DynectGetError as error:
        if 'No such zone' in str(error):
            module.fail_json(
                msg="Not a valid zone for this account",
                zone=module.params['zone'])
        else:
            module.fail_json(msg="Unable to retrieve zone", error=str(error))

    # To retrieve the node object we need to remove the zone name from the FQDN
    dyn_node_name = module.params['record_fqdn'].\
        replace('.' + module.params['zone'], '')

    # Retrieve the zone object from dyn
    dyn_zone = Zone(module.params['zone'])

    # Retrieve the node object from dyn
    dyn_node = dyn_zone.get_node(node=dyn_node_name)

    # All states will need a list of the exiting records for the zone.
    dyn_node_records = get_any_records(module, dyn_node)

    dyn_values = get_record_values(dyn_node_records)

    if module.params['state'] == 'list':
        module.exit_json(changed=False, dyn_records=dyn_values)

    elif module.params['state'] == 'absent':
        # If there are any records present we'll want to delete the node.
        if dyn_node_records:
            dyn_node.delete()

            # Publish the zone since we've modified it.
            dyn_zone.publish()

            module.exit_json(
                changed=True,
                msg="Removed node %s from zone %s" % (dyn_node_name,
                                                      module.params['zone'])
            )

        module.exit_json(changed=False)

    elif module.params['state'] == 'present':

        # configure the TTL variable:
        # if use_zone_ttl, use the default TTL of the account.
        # if TTL == None, don't check it, set it as 0 (api default)
        # if TTL > 0, ensure this TTL is set
        if module.params['use_zone_ttl']:
            user_param_ttl = dyn_zone.ttl
        elif not module.params['record_ttl']:
            user_param_ttl = 0
        else:
            user_param_ttl = module.params['record_ttl']

        # First get a list of existing records for the node
        record_type_key = get_record_key(module.params['record_type'])
        user_record_value = module.params['record_value']

        ########
        # CREATE
        ########
        # Check to see if the record is already in place before doing anything.
        # If there are no records for this node, create it.
        if not dyn_node_records:
            record = dyn_zone.add_record(dyn_node_name,
                                         module.params['record_type'],
                                         module.params['record_value'],
                                         user_param_ttl)
        ########
        # UPDATE
        ########
        elif compare_record_values(record_type_key,
                                   user_record_value,
                                   dyn_values):
            if user_param_ttl == 0 or \
               compare_record_ttl(record_type_key,
                                  user_record_value,
                                  dyn_values,
                                  user_param_ttl):
                module.exit_json(changed=False, dyn_record=dyn_values)

            record = update_record_values(dyn_node_records,
                                          module.params['record_type'],
                                          module.params['record_value'],
                                          user_param_ttl)
        # remove the record as it is not the same type as the requested
        else:
            dyn_node.delete()
            # Now lets create the correct node entry.
            record = dyn_zone.add_record(dyn_node_name,
                                         module.params['record_type'],
                                         module.params['record_value'],
                                         user_param_ttl)

        # Now publish the zone since we've updated/created it.
        dyn_zone.publish()

        rmsg = "Created node {} in zone {}".format(
            dyn_node_name,
            module.params['zone'])
        module.exit_json(
            changed=True,
            msg=rmsg,
            dyn_record=get_record_values({record_type_key: [record]}))

    module.fail_json(msg="Unknown state: [%s]" % module.params['state'])


if __name__ == '__main__':
    main()
