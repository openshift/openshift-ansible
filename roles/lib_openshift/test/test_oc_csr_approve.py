import os
import sys

import pytest

from ansible.module_utils.basic import AnsibleModule

try:
    # python3, mock is built in.
    from unittest.mock import patch
except ImportError:
    # In python2, mock is installed via pip.
    from mock import patch

MODULE_PATH = os.path.realpath(os.path.join(__file__, os.pardir, os.pardir, 'library'))
sys.path.insert(1, MODULE_PATH)

import oc_csr_approve  # noqa

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


def test_get_ready_nodes():
    output_file = os.path.join(ASSET_PATH, 'oc_get_nodes.json')
    with open(output_file) as stdoutfile:
        oc_get_nodes_stdout = stdoutfile.read()

    module = DummyModule({})

    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (0, oc_get_nodes_stdout, '')
        ready_nodes = oc_csr_approve.get_ready_nodes(module, 'oc', '/dev/null')
    assert ready_nodes == ['fedora1.openshift.io', 'fedora3.openshift.io']


def test_get_csrs():
    module = DummyModule({})
    output_file = os.path.join(ASSET_PATH, 'oc_csr_approve_pending.json')
    with open(output_file) as stdoutfile:
        oc_get_csr_out = stdoutfile.read()

    # mock oc get csr call to cluster
    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (0, oc_get_csr_out, '')
        csrs = oc_csr_approve.get_csrs(module, 'oc', '/dev/null')

    assert csrs[0]['kind'] == "CertificateSigningRequest"

    output_file = os.path.join(ASSET_PATH, 'openssl1.txt')
    with open(output_file) as stdoutfile:
        openssl_out = stdoutfile.read()

    # mock openssl req call.
    node_list = ['fedora2.mguginolocal.com']
    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (0, openssl_out, '')
        csr_dict = oc_csr_approve.process_csrs(module, csrs, node_list, "client")
    # actually run openssl req call.
    csr_dict = oc_csr_approve.process_csrs(module, csrs, node_list, "client")
    assert csr_dict['node-csr-TkefytQp8Dz4Xp7uzcw605MocvI0gWuEOGNrHhOjGNQ'] == 'fedora2.mguginolocal.com'


def test_confirm_needed_requests_present():
    module = DummyModule({})
    csr_dict = {'some-csr': 'fedora1.openshift.io'}
    not_ready_nodes = ['host1']
    with pytest.raises(Exception) as err:
        oc_csr_approve.confirm_needed_requests_present(
            module, not_ready_nodes, csr_dict)
    assert 'Exception: Could not find csr for nodes: host1' in str(err)

    not_ready_nodes = ['fedora1.openshift.io']
    # this should complete silently
    oc_csr_approve.confirm_needed_requests_present(
        module, not_ready_nodes, csr_dict)


def test_approve_csrs():
    module = DummyModule({})
    oc_bin = 'oc'
    oc_conf = '/dev/null'
    csr_dict = {'csr-1': 'example.openshift.io'}
    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (0, 'csr-1 ok', '')
        client_approve_results = oc_csr_approve.approve_csrs(
            module, oc_bin, oc_conf, csr_dict, 'client')
    assert client_approve_results == ['csr-1 ok']


def test_get_ready_nodes_server():
    module = DummyModule({})
    oc_bin = 'oc'
    oc_conf = '/dev/null'
    nodes_list = ['fedora1.openshift.io']
    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (0, 'ok', '')
        ready_nodes_server = oc_csr_approve.get_ready_nodes_server(
            module, oc_bin, oc_conf, nodes_list)
    assert ready_nodes_server == ['fedora1.openshift.io']


def test_get_csrs_server():
    module = DummyModule({})
    output_file = os.path.join(ASSET_PATH, 'oc_csr_server_multiple_pends_one_host.json')
    with open(output_file) as stdoutfile:
        oc_get_csr_out = stdoutfile.read()

    # mock oc get csr call to cluster
    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (0, oc_get_csr_out, '')
        csrs = oc_csr_approve.get_csrs(module, 'oc', '/dev/null')

    assert csrs[0]['kind'] == "CertificateSigningRequest"

    output_file = os.path.join(ASSET_PATH, 'openssl1.txt')
    with open(output_file) as stdoutfile:
        openssl_out = stdoutfile.read()

    node_list = ['fedora1.openshift.io']

    # mock openssl req call.
    with patch(RUN_CMD_MOCK) as call_mock:
        call_mock.return_value = (0, openssl_out, '')
        csr_dict = oc_csr_approve.process_csrs(module, csrs, node_list, "server")

    # actually run openssl req call.
    node_list = ['fedora2.mguginolocal.com']
    csr_dict = oc_csr_approve.process_csrs(module, csrs, node_list, "server")
    assert csr_dict['csr-2cxkp'] == 'fedora2.mguginolocal.com'


def test_verify_server_csrs():
    module = DummyModule({})
    oc_bin = 'oc'
    oc_conf = '/dev/null'
    result = {}
    ready_nodes_server = ['fedora1.openshift.io']
    node_list = ['fedora1.openshift.io']
    with patch('oc_csr_approve.get_ready_nodes_server') as call_mock:
        call_mock.return_value = ready_nodes_server
        # This should silently return
        oc_csr_approve.verify_server_csrs(module, result, oc_bin, oc_conf,
                                          node_list)

    node_list = ['fedora1.openshift.io', 'fedora2.openshift.io']
    with patch('oc_csr_approve.get_ready_nodes_server') as call_mock:
        call_mock.return_value = ready_nodes_server
        with pytest.raises(Exception) as err:
            oc_csr_approve.verify_server_csrs(module, result, oc_bin, oc_conf,
                                              node_list)
        assert 'after approving server certs: fedora2.openshift.io' in str(err)


if __name__ == '__main__':
    test_parse_subject_cn()
    test_get_ready_nodes()
    test_get_csrs()
    test_confirm_needed_requests_present()
    test_approve_csrs()
    test_get_ready_nodes_server()
    test_get_csrs_server()
    test_verify_server_csrs()
