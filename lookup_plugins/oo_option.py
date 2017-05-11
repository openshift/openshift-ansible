#!/usr/bin/env python2
# -*- coding: utf-8 -*-
'''
oo_option lookup plugin for openshift-ansible

Usage:

    - debug:
      msg: "{{ lookup('oo_option', '<key>') | default('<default_value>', True) }}"

This returns, by order of priority:

* if it exists, the `cli_<key>` ansible variable. This variable is set by `bin/cluster --option <key>=<value> …`
* if it exists, the envirnoment variable named `<key>`
* if none of the above conditions are met, empty string is returned
'''


import os

# pylint: disable=no-name-in-module,import-error,unused-argument,unused-variable,super-init-not-called,too-few-public-methods,missing-docstring
try:
    # ansible-2.0
    from ansible.plugins.lookup import LookupBase
except ImportError:
    # ansible-1.9.x
    class LookupBase(object):
        def __init__(self, basedir=None, runner=None, **kwargs):
            self.runner = runner
            self.basedir = self.runner.basedir

            def get_basedir(self, variables):
                return self.basedir


# Reason: disable too-few-public-methods because the `run` method is the only
#     one required by the Ansible API
# Status: permanently disabled
# pylint: disable=too-few-public-methods
class LookupModule(LookupBase):
    ''' oo_option lookup plugin main class '''

    # Reason: disable unused-argument because Ansible is calling us with many
    #     parameters we are not interested in.
    #     The lookup plugins of Ansible have this kwargs “catch-all” parameter
    #     which is not used
    # Status: permanently disabled unless Ansible API evolves
    # pylint: disable=unused-argument
    def __init__(self, basedir=None, **kwargs):
        ''' Constructor '''
        self.basedir = basedir

    # Reason: disable unused-argument because Ansible is calling us with many
    #     parameters we are not interested in.
    #     The lookup plugins of Ansible have this kwargs “catch-all” parameter
    #     which is not used
    # Status: permanently disabled unless Ansible API evolves
    # pylint: disable=unused-argument
    def run(self, terms, variables, **kwargs):
        ''' Main execution path '''

        ret = []

        for term in terms:
            option_name = term.split()[0]
            cli_key = 'cli_' + option_name
            if 'vars' in variables and cli_key in variables['vars']:
                ret.append(variables['vars'][cli_key])
            elif option_name in os.environ:
                ret.append(os.environ[option_name])
            else:
                ret.append('')

        return ret
