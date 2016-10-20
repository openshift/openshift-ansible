#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4
"""
Custom filters for use in openshift-ansible
"""

from ansible import errors
from collections import Mapping
from distutils.util import strtobool
from distutils.version import LooseVersion
from operator import itemgetter
import OpenSSL.crypto
import os
import pdb
import pkg_resources
import re
import json
import yaml
from ansible.parsing.yaml.dumper import AnsibleDumper
from urlparse import urlparse

try:
    # ansible-2.2
    # ansible.utils.unicode.to_unicode is deprecated in ansible-2.2,
    # ansible.module_utils._text.to_text should be used instead.
    from ansible.module_utils._text import to_text
except ImportError:
    # ansible-2.1
    from ansible.utils.unicode import to_unicode as to_text

# Disabling too-many-public-methods, since filter methods are necessarily
# public
# pylint: disable=too-many-public-methods
class FilterModule(object):
    """ Custom ansible filters """

    @staticmethod
    def oo_cert_expiry_results_to_json(hostvars, play_hosts):
        """Takes results (`hostvars`) from the openshift_cert_expiry role
check and serializes them into proper machine-readable JSON
output. This filter parameter **MUST** be the playbook `hostvars`
variable. The `play_hosts` parameter is so we know what to loop over
when we're extrating the values.

Returns:

Results are collected into two top-level keys under the `json_results`
dict:

* `json_results.data` [dict] - Each individual host check result, keys are hostnames
* `json_results.summary` [dict] - Summary of number of `warning` and `expired`
certificates

Example playbook usage:

  - name: Generate expiration results JSON
    become: no
    run_once: yes
    delegate_to: localhost
    when: "{{ openshift_certificate_expiry_save_json_results|bool }}"
    copy:
      content: "{{ hostvars|oo_cert_expiry_results_to_json() }}"
      dest: "{{ openshift_certificate_expiry_json_results_path }}"

        """
        json_result = {
            'data': {},
            'summary': {},
        }

        for host in play_hosts:
            json_result['data'][host] = hostvars[host]['check_results']['check_results']

        total_warnings = sum([hostvars[h]['check_results']['summary']['warning'] for h in play_hosts])
        total_expired = sum([hostvars[h]['check_results']['summary']['expired'] for h in play_hosts])

        json_result['summary']['warning'] = total_warnings
        json_result['summary']['expired'] = total_expired

        return json_result


    def filters(self):
        """ returns a mapping of filters to methods """
        return {
            "oo_cert_expiry_results_to_json": self.oo_cert_expiry_results_to_json,
        }
