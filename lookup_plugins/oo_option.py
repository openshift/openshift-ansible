#!/usr/bin/env python2
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4

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

from ansible.utils import template
import os

# Reason: disable too-few-public-methods because the `run` method is the only
#     one required by the Ansible API
# Status: permanently disabled
# pylint: disable=too-few-public-methods
class LookupModule(object):
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
    def run(self, terms, inject=None, **kwargs):
        ''' Main execution path '''

        try:
            terms = template.template(self.basedir, terms, inject)
        # Reason: disable broad-except to really ignore any potential exception
        #         This is inspired by the upstream "env" lookup plugin:
        #         https://github.com/ansible/ansible/blob/devel/v1/ansible/runner/lookup_plugins/env.py#L29
        # pylint: disable=broad-except
        except Exception:
            pass

        if isinstance(terms, basestring):
            terms = [terms]

        ret = []

        for term in terms:
            option_name = term.split()[0]
            cli_key = 'cli_' + option_name
            if inject and cli_key in inject:
                ret.append(inject[cli_key])
            elif option_name in os.environ:
                ret.append(os.environ[option_name])
            else:
                ret.append('')

        return ret
