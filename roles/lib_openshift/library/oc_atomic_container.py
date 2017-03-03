#!/usr/bin/env python
# pylint: disable=missing-docstring
# flake8: noqa: T001
#     ___ ___ _  _ ___ ___    _ _____ ___ ___
#    / __| __| \| | __| _ \  /_\_   _| __|   \
#   | (_ | _|| .` | _||   / / _ \| | | _|| |) |
#    \___|___|_|\_|___|_|_\/_/_\_\_|_|___|___/_ _____
#   |   \ / _ \  | \| |/ _ \_   _| | __|   \_ _|_   _|
#   | |) | (_) | | .` | (_) || |   | _|| |) | |  | |
#   |___/ \___/  |_|\_|\___/ |_|   |___|___/___| |_|
#
# Copyright 2016 Red Hat, Inc. and/or its affiliates
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
#

# -*- -*- -*- Begin included fragment: doc/atomic_container -*- -*- -*-

DOCUMENTATION = '''
---
module: oc_atomic_container
short_description: Manage the container images on the atomic host platform
description:
    - Manage the container images on the atomic host platform
    - Allows to execute the commands on the container images
requirements:
  - atomic
  - "python >= 2.6"
options:
    name:
        description:
          - Name of the container
        required: True
        default: null
    image:
        description:
          - The image to use to install the container
        required: True
        default: null
    state:
        description:
          - State of the container
        required: True
        choices: ["latest", "absent", "latest", "rollback"]
        default: "latest"
    values:
        description:
          - Values for the installation of the container
        required: False
        default: None
'''

# -*- -*- -*- End included fragment: doc/atomic_container -*- -*- -*-

# -*- -*- -*- Begin included fragment: ansible/oc_atomic_container.py -*- -*- -*-

# pylint: disable=wrong-import-position,too-many-branches,invalid-name
import json
from ansible.module_utils.basic import AnsibleModule


def _install(module, container, image, values_list):
    ''' install a container using atomic CLI.  values_list is the list of --set arguments.
    container is the name given to the container.  image is the image to use for the installation. '''
    args = ['atomic', 'install', "--system", '--name=%s' % container] + values_list + [image]
    rc, out, err = module.run_command(args, check_rc=False)
    if rc != 0:
        return rc, out, err, False
    else:
        changed = "Extracting" in out
        return rc, out, err, changed

def _uninstall(module, name):
    ''' uninstall an atomic container by its name. '''
    args = ['atomic', 'uninstall', name]
    rc, out, err = module.run_command(args, check_rc=False)
    return rc, out, err, False


def do_install(module, container, image, values_list):
    ''' install a container and exit the module. '''
    rc, out, err, changed = _install(module, container, image, values_list)
    if rc != 0:
        module.fail_json(rc=rc, msg=err)
    else:
        module.exit_json(msg=out, changed=changed)


def do_uninstall(module, name):
    ''' uninstall a container and exit the module. '''
    rc, out, err, changed = _uninstall(module, name)
    if rc != 0:
        module.fail_json(rc=rc, msg=err)
    module.exit_json(msg=out, changed=changed)


def do_update(module, container, old_image, image, values_list):
    ''' update a container and exit the module.  If the container uses a different
    image than the current installed one, then first uninstall the old one '''

    # the image we want is different than the installed one
    if old_image != image:
        rc, out, err, _ = _uninstall(module, container)
        if rc != 0:
            module.fail_json(rc=rc, msg=err)
        return do_install(module, container, image, values_list)

    # if the image didn't change, use "atomic containers update"
    args = ['atomic', 'containers', 'update'] + values_list + [container]
    rc, out, err = module.run_command(args, check_rc=False)
    if rc != 0:
        module.fail_json(rc=rc, msg=err)
    else:
        changed = "Extracting" in out
        module.exit_json(msg=out, changed=changed)


def do_rollback(module, name):
    ''' move to the previous deployment of the container, if present, and exit the module. '''
    args = ['atomic', 'containers', 'rollback', name]
    rc, out, err = module.run_command(args, check_rc=False)
    if rc != 0:
        module.fail_json(rc=rc, msg=err)
    else:
        changed = "Rolling back" in out
        module.exit_json(msg=out, changed=changed)


def core(module):
    ''' entrypoint for the module. '''
    name = module.params['name']
    image = module.params['image']
    values = module.params['values']
    state = module.params['state']

    module.run_command_environ_update = dict(LANG='C', LC_ALL='C', LC_MESSAGES='C')
    out = {}
    err = {}
    rc = 0

    values_list = ["--set=%s" % x for x in values] if values else []

    args = ['atomic', 'containers', 'list', '--json', '--all', '-f', 'container=%s' % name]
    rc, out, err = module.run_command(args, check_rc=False)
    if rc != 0:
        module.fail_json(rc=rc, msg=err)
        return

    containers = json.loads(out)
    present = len(containers) > 0
    old_image = containers[0]["image_name"] if present else None

    if state == 'present' and present:
        module.exit_json(msg=out, changed=False)
    elif (state in ['latest', 'present']) and not present:
        do_install(module, name, image, values_list)
    elif state == 'latest':
        do_update(module, name, old_image, image, values_list)
    elif state == 'absent':
        if not present:
            module.exit_json(msg="", changed=False)
        else:
            do_uninstall(module, name)
    elif state == 'rollback':
        do_rollback(module, name)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(default=None, required=True),
            image=dict(default=None, required=True),
            state=dict(default='latest', choices=['present', 'absent', 'latest', 'rollback']),
            values=dict(type='list', default=[]),
            ),
        )

    # Verify that the platform supports atomic command
    rc, _, err = module.run_command('atomic -v', check_rc=False)
    if rc != 0:
        module.fail_json(msg="Error in running atomic command", err=err)

    try:
        core(module)
    except Exception as e:  # pylint: disable=broad-except
        module.fail_json(msg=str(e))


if __name__ == '__main__':
    main()

# -*- -*- -*- End included fragment: ansible/oc_atomic_container.py -*- -*- -*-
