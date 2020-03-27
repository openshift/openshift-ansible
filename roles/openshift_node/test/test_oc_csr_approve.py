import os
import sys
from unittest.mock import patch

from ansible.module_utils.basic import AnsibleModule

MODULE_PATH = os.path.realpath(os.path.join(__file__, os.pardir, os.pardir, 'library'))
sys.path.insert(1, MODULE_PATH)

import oc_csr_approve  # noqa
from oc_csr_approve import CSRapprove # noqa

# base path for text files with sample outputs.
ASSET_PATH = os.path.realpath(os.path.join(__file__, os.pardir, 'test_data'))

RUN_CMD_MOCK = 'ansible.module_utils.basic.AnsibleModule.run_command'


class DummyModule(AnsibleModule):
    def _load_params(self):
        self.params = {}

    def exit_json(*args, **kwargs):
        return 0

    def fail_json(*args, **kwargs):
        raise Exception(kwargs['msg'])


def test_parse_subject_cn():
    subject = 'subject=/C=US/CN=fedora1.openshift.io/L=Raleigh/O=Red Hat/ST=North Carolina/OU=OpenShift\n'
    assert oc_csr_approve.parse_subject_cn(subject) == 'fedora1.openshift.io'

    subject = 'subject=C = US, CN = test.io, L = City, O = Company, ST = State, OU = Dept\n'
    assert oc_csr_approve.parse_subject_cn(subject) == 'test.io'


def test_csr_present_check():
    csr_dict = {'csr-1': 'fedora1.openshift.io'}

    nodename = 'fedora1.openshift.io'
    assert oc_csr_approve.csr_present_check(nodename, csr_dict) is True

    nodename = 'fedora2.openshift.io'
    assert oc_csr_approve.csr_present_check(nodename, csr_dict) is False


def test_get_nodes():
    output_file = os.path.join(ASSET_PATH, 'oc_get_nodes.json')
    with open(output_file) as stdoutfile:
        oc_get_nodes_stdout = stdoutfile.read()

    module = DummyModule({})
    approver = CSRapprove(module, 'oc', '/dev/null', [])

    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (0, oc_get_nodes_stdout, '')
        all_nodes = approver.get_nodes()
    assert all_nodes == ['fedora1.openshift.io', 'fedora2.openshift.io', 'fedora3.openshift.io']


def test_get_csrs_client():
    module = DummyModule({})
    approver = CSRapprove(module, 'oc', '/dev/null', [])
    output_file = os.path.join(ASSET_PATH, 'oc_csr_approve_pending.json')
    with open(output_file) as stdoutfile:
        oc_get_csr_out = stdoutfile.read()

    # mock oc get csr call to cluster
    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (0, oc_get_csr_out, '')
        csrs = approver.get_csrs()

    assert csrs[0]['kind'] == "CertificateSigningRequest"

    output_file = os.path.join(ASSET_PATH, 'openssl1.txt')
    with open(output_file) as stdoutfile:
        openssl_out = stdoutfile.read()

    # mock openssl req call.
    nodename = 'fedora1.openshift.io'
    approver = CSRapprove(module, 'oc', '/dev/null', nodename)
    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (0, openssl_out, '')
        csr_dict = approver.process_csrs(csrs, "client")
    # actually run openssl req call.
    csr_dict = approver.process_csrs(csrs, "client")
    assert csr_dict['node-csr-TkefytQp8Dz4Xp7uzcw605MocvI0gWuEOGNrHhOjGNQ'] == 'fedora1.openshift.io'


def test_get_csrs_server():
    module = DummyModule({})
    output_file = os.path.join(ASSET_PATH, 'oc_csr_server_multiple_pends_one_host.json')
    with open(output_file) as stdoutfile:
        oc_get_csr_out = stdoutfile.read()

    approver = CSRapprove(module, 'oc', '/dev/null', [])
    # mock oc get csr call to cluster
    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (0, oc_get_csr_out, '')
        csrs = approver.get_csrs()

    assert csrs[0]['kind'] == "CertificateSigningRequest"

    output_file = os.path.join(ASSET_PATH, 'openssl1.txt')
    with open(output_file) as stdoutfile:
        openssl_out = stdoutfile.read()

    nodename = 'fedora1.openshift.io'
    approver = CSRapprove(module, 'oc', '/dev/null', nodename)
    # mock openssl req call.
    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (0, openssl_out, '')
        csr_dict = approver.process_csrs(csrs, "server")

    # actually run openssl req call.
    nodename = 'fedora1.openshift.io'
    approver = CSRapprove(module, 'oc', '/dev/null', nodename)
    csr_dict = approver.process_csrs(csrs, "server")
    assert csr_dict['csr-2cxkp'] == 'fedora1.openshift.io'


def test_process_csrs():
    module = DummyModule({})
    approver = CSRapprove(module, 'oc', '/dev/null', 'fedora1.openshift.io')
    output_file = os.path.join(ASSET_PATH, 'oc_csr_approve_pending.json')
    with open(output_file) as stdoutfile:
        oc_get_csr_out = stdoutfile.read()

    # mock oc get csr call to cluster
    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (0, oc_get_csr_out, '')
        csrs = approver.get_csrs()

    csr_dict = approver.process_csrs(csrs, "client")
    assert csr_dict == {'node-csr-TkefytQp8Dz4Xp7uzcw605MocvI0gWuEOGNrHhOjGNQ': 'fedora1.openshift.io'}


def test_approve_csrs():
    module = DummyModule({})
    csr_dict = {'csr-1': 'fedora1.openshift.io'}
    approver = CSRapprove(module, 'oc', '/dev/null', '')
    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (0, 'csr-1 ok', '')
        approver.approve_csrs(csr_dict, 'client')
    assert approver.result['client_approve_results'] == ['fedora1.openshift.io: csr-1 ok']


def test_node_is_ready():
    module = DummyModule({})
    nodename = 'fedora1.openshift.io'
    approver = CSRapprove(module, 'oc', '/dev/null', nodename)
    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (0, 'ok', '')
        result = approver.node_is_ready(nodename)
    assert result is True

    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (1, 'stdout fail', 'stderr fail')
        result = approver.node_is_ready(nodename)
    assert result is False
