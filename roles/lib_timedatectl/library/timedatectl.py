#!/usr/bin/env python
'''
    timedatectl ansible module

    This module supports setting ntp enabled
'''
import subprocess




def do_timedatectl(options=None):
    ''' subprocess timedatectl '''

    cmd = ['/usr/bin/timedatectl']
    if options:
        cmd += options.split()

    proc = subprocess.Popen(cmd, stdin=None, stdout=subprocess.PIPE)
    proc.wait()
    return proc.stdout.read()

def main():
    ''' Ansible module for timedatectl
    '''

    module = AnsibleModule(
        argument_spec=dict(
            #state=dict(default='enabled', type='str'),
            ntp=dict(default=True, type='bool'),
        ),
        #supports_check_mode=True
    )

    # do something
    ntp_enabled = False

    results = do_timedatectl()

    for line in results.split('\n'):
        if 'NTP enabled' in line:
            if 'yes' in line:
                ntp_enabled = True

    ########
    # Enable NTP
    ########
    if module.params['ntp']:
        if ntp_enabled:
            module.exit_json(changed=False, results="enabled", state="enabled")

        # Enable it
        # Commands to enable ntp
        else:
            results = do_timedatectl('set-ntp yes')
            module.exit_json(changed=True, results="enabled", state="enabled", cmdout=results)

    #########
    # Disable NTP
    #########
    else:
        if not ntp_enabled:
            module.exit_json(changed=False, results="disabled", state="disabled")

        results = do_timedatectl('set-ntp no')
        module.exit_json(changed=True, results="disabled", state="disabled")

    module.exit_json(failed=True, changed=False, results="Something went wrong", state="unknown")

# Pylint is getting in the way of basic Ansible
# pylint: disable=redefined-builtin,wildcard-import,unused-wildcard-import
from ansible.module_utils.basic import *

main()
