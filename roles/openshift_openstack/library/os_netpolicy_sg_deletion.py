#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright 2018 Red Hat, Inc. and/or its affiliates
# and other contributors as indicated by the @author tags.
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


# pylint: disable=unused-wildcard-import,wildcard-import,unused-import,redefined-builtin

''' os_netpolicy_sg_deletions '''
import keystoneauth1

from ansible.module_utils.basic import AnsibleModule

try:
    import shade
    HAS_SHADE = True
except ImportError:
    HAS_SHADE = False

DOCUMENTATION = '''
---
module: os_netpolicy_sg_deletions
short_description: Delete security group associated to the network policy
description:
    - Delete the security group associated to the network policy
author:
    - "Luis Tomas Bolivar <ltomasbo@redhat.com>"
'''

RETURN = '''
'''


def main():
    ''' Main module function '''
    module = AnsibleModule(
        argument_spec=dict(
            sg_id=dict(default=False, type='str'),
        ),
        supports_check_mode=True,
    )

    if not HAS_SHADE:
        module.fail_json(msg='shade is required for this module')

    try:
        cloud = shade.openstack_cloud()
    # pylint: disable=broad-except
    except Exception:
        module.fail_json(msg='Failed to connect to the cloud')

    try:
        adapter = keystoneauth1.adapter.Adapter(
            session=cloud.keystone_session,
            service_type=cloud.cloud_config.get_service_type('network'),
            interface=cloud.cloud_config.get_interface('network'),
            endpoint_override=cloud.cloud_config.get_endpoint('network'),
            version=cloud.cloud_config.get_api_version('network'))
    # pylint: disable=broad-except
    except Exception:
        module.fail_json(msg='Failed to get an adapter to talk to the Neutron '
                             'API')

    try:
        if module.params.get('sg_id'):
            adapter.delete('/security-groups/' + module.params['sg_id'])
    # pylint: disable=broad-except
    except Exception:
        module.fail_json(msg='Failed to delete Security group associated to '
                         'the network policy')

    module.exit_json(
        changed=True)


if __name__ == '__main__':
    main()
