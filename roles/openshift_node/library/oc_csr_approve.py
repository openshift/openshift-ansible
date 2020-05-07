#!/usr/bin/env python
"""oc_csr_approve module"""
# Copyright 2020 Red Hat, Inc. and/or its affiliates
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

import base64
import json
import time

from ansible.module_utils.basic import AnsibleModule

try:
    # Python >= 3.5
    from json.decoder import JSONDecodeError
except ImportError:
    # Python < 3.5
    JSONDecodeError = ValueError

DOCUMENTATION = '''
---
module: oc_csr_approve

short_description: Retrieve and approve node client and server CSRs

version_added: "2.9"

description:
    - Retrieve and approve node client and server CSRs

author:
    - "Michael Gugino <mgugino@redhat.com>"
    - "Russell Teague <rteague@redhat.com>"
'''

EXAMPLES = '''
- name: Approve node CSRs
  oc_csr_approve:
    kubeconfig: "{{ openshift_node_kubeconfig_path }}"
    nodename: "{{ ansible_nodename | lower }}"
  delegate_to: localhost
'''

CERT_MODE = {'client': 'client auth', 'server': 'server auth'}


def parse_subject_cn(subject_str):
    """parse output of openssl req -noout -subject to retrieve CN.
       example input:
         'subject=/C=US/CN=test.io/L=Raleigh/O=Red Hat/ST=North Carolina/OU=OpenShift\n'
         or
         'subject=C = US, CN = test.io, L = City, O = Company, ST = State, OU = Dept\n'
       example output: 'test.io'
    """
    stripped_string = subject_str[len('subject='):].strip()
    kv_strings = [x.strip() for x in stripped_string.split(',')]
    if len(kv_strings) == 1:
        kv_strings = [x.strip() for x in stripped_string.split('/')][1:]
    for item in kv_strings:
        item_parts = [x.strip() for x in item.split('=')]
        if item_parts[0] == 'CN':
            return item_parts[1]
    return None


def csr_present_check(nodename, csr_dict):
    """Ensure node has a CSR
    Returns True if CSR for node is present"""
    for _, val in csr_dict.items():
        if val == nodename:
            # CSR for node is present
            return True
    # Didn't find a CSR for node
    return False


class CSRapprove(object):  # pylint: disable=useless-object-inheritance
    """Approves node CSRs"""

    def __init__(self, module, oc_bin, kubeconfig, nodename):
        """init method"""
        self.module = module
        self.oc_bin = oc_bin
        self.kubeconfig = kubeconfig
        self.nodename = nodename
        # Build a dictionary to hold all of our output information so nothing
        # is lost when we fail.
        self.result = {'changed': False,
                       'rc': 0,
                       'client_approve_results': [],
                       'server_approve_results': [],
                       }

    def run_command(self, command, rc_opts=None):
        """Run a command using AnsibleModule.run_command, or fail"""
        if rc_opts is None:
            rc_opts = {}
        rtnc, stdout, err = self.module.run_command(command, **rc_opts)
        if rtnc:
            self.result['failed'] = True
            self.result['rc'] = rtnc
            self.result['msg'] = str(err)
            self.result['state'] = 'unknown'
            self.module.fail_json(**self.result)
        return stdout

    def get_nodes(self):
        """Get all nodes via oc get nodes -ojson"""
        # json output is necessary for consistency here.
        command = "{} {} get nodes -ojson".format(self.oc_bin, self.kubeconfig)
        stdout = self.run_command(command)
        try:
            data = json.loads(stdout)
        except JSONDecodeError as err:
            self.result['failed'] = True
            self.result['rc'] = 1
            self.result['msg'] = str(err)
            self.result['state'] = 'unknown'
            self.module.fail_json(**self.result)
        return [node['metadata']['name'] for node in data['items']]

    def get_csrs(self):
        """Retrieve CSRs from cluster using oc get csr -ojson"""
        command = "{} {} get csr -ojson".format(self.oc_bin, self.kubeconfig)
        stdout = self.run_command(command)
        try:
            data = json.loads(stdout)
        except JSONDecodeError as err:
            self.result['failed'] = True
            self.result['rc'] = 1
            self.result['msg'] = str(err)
            self.result['state'] = 'unknown'
            self.module.fail_json(**self.result)
        return data['items']

    def process_csrs(self, csrs, mode):
        """Return a dictionary of pending CSRs where the format of the dict is
           k=csr name, v=Subject Common Name"""
        csr_dict = {}
        for item in csrs:
            status = item['status'].get('conditions')
            if status:
                # If status is not an empty dictionary, cert is not pending.
                continue
            if CERT_MODE[mode] not in item['spec']['usages']:
                continue

            name = item['metadata']['name']
            request_data = base64.b64decode(item['spec']['request'])
            command = "openssl req -noout -subject"
            # ansible's module.run_command accepts data to pipe via stdin as
            # as 'data' kwarg.
            rc_opts = {'data': request_data, 'binary_data': True}
            stdout = self.run_command(command, rc_opts=rc_opts)

            # parse common_name from subject string.
            common_name = parse_subject_cn(stdout)
            if common_name and common_name.startswith('system:node:'):
                # common name is typically prepended with system:node:.
                common_name = common_name.split('system:node:')[1]
            # we only want to approve CSRs from nodes we know about.
            if common_name == self.nodename:
                csr_dict[name] = common_name

        return csr_dict

    def approve_csrs(self, csr_pending_list, mode):
        """Loop through csr_pending_list and call:
           oc adm certificate approve <item>"""
        results_mode = "{}_approve_results".format(mode)
        base_command = "{} {} adm certificate approve {}"
        approve_results = []
        for csr in csr_pending_list:
            command = base_command.format(self.oc_bin, self.kubeconfig, csr)
            rtnc, stdout, err = self.module.run_command(command)
            if rtnc:
                self.result['failed'] = True
                self.result['rc'] = rtnc
                self.result['msg'] = str(err)
                self.result[results_mode].extend(approve_results)
                self.result['state'] = 'unknown'
                self.module.fail_json(**self.result)
            approve_results.append("{}: {}".format(csr_pending_list[csr], stdout))
        self.result[results_mode].extend(approve_results)

        # We set changed for approved client or server CSRs.
        self.result['changed'] = bool(approve_results) or bool(self.result['changed'])

    def node_is_ready(self, nodename):
        """Determine if node has working server certificate
        Returns True if the node is ready"""
        base_command = "{} {} get --raw /api/v1/nodes/{}/proxy/healthz"
        # need this to look like /api/v1/nodes/<node>/proxy/healthz
        # if we can hit that api endpoint (rtnc=0), the node has a valid server cert.
        command = base_command.format(self.oc_bin, self.kubeconfig, nodename)
        rtnc, _, _ = self.module.run_command(command)
        return not bool(rtnc)

    def runner(self, attempts, mode):
        """Approve CSRs if they are present for node"""
        results_mode = "{}_approve_results".format(mode)
        # Get all CSRs, no good way to filter on pending.
        csrs = self.get_csrs()
        # process data in CSRs and build a dictionary of requests
        csr_dict = self.process_csrs(csrs, mode)

        if csr_present_check(self.nodename, csr_dict):
            # Approve outstanding CSRs for node
            self.approve_csrs(csr_dict, mode)
        else:
            # CSR is not present, increment attempts and retry
            if attempts < 36:  # 36 * 5 = 3 minutes waiting for CSRs
                self.result[results_mode].append(
                    "Attempt: {}, Node {} not present or CSR not yet available".format(attempts, self.nodename))
                attempts += 1
                time.sleep(5)
            else:
                # If attempts < 36, fail waiting for CSRs to appear
                # Using 'describe' to have the API provide the decoded results for all CSRs
                command = "{} {} describe csr".format(self.oc_bin, self.kubeconfig)
                stdout = self.run_command(command)
                self.result['failed'] = True
                self.result['rc'] = 1
                self.result['msg'] = "Node {} not present or could not find {} CSR".format(self.nodename, mode)
                self.result['oc_describe_csr'] = stdout
                self.module.fail_json(**self.result)

        return attempts

    def run(self):
        """execute the CSR approval process"""

        # # Client Cert Section # #
        mode = "client"
        attempts = 1
        while True:
            # If the node is in the list of all nodes, we do not need to approve client CSRs
            if self.nodename not in self.get_nodes():
                attempts = self.runner(attempts, mode)
            else:
                self.result["{}_approve_results".format(mode)].append(
                    "Node {} is present in node list".format(self.nodename))
                break

        # # Server Cert Section # #
        mode = "server"
        attempts = 1
        while True:
            # If the node API is healthy, we do not need to approve server CSRs
            if not self.node_is_ready(self.nodename):
                attempts = self.runner(attempts, mode)
            else:
                self.result["{}_approve_results".format(mode)].append(
                    "Node {} API is ready".format(self.nodename))
                break

        self.module.exit_json(**self.result)


def run_module():
    """Run this module"""
    module_args = dict(
        oc_bin=dict(type='path', required=False, default='oc'),
        kubeconfig=dict(type='path', required=True),
        nodename=dict(type='str', required=True),
    )
    module = AnsibleModule(
        supports_check_mode=False,
        argument_spec=module_args
    )
    oc_bin = module.params['oc_bin']
    kubeconfig = '--kubeconfig={}'.format(module.params['kubeconfig'])
    nodename = module.params['nodename']

    approver = CSRapprove(module, oc_bin, kubeconfig, nodename)
    approver.run()


def main():
    """main"""
    run_module()


if __name__ == '__main__':
    main()
