#!/usr/bin/env python
'''
 Unit tests for the FakeOpenSSL classes
'''

import os
import sys
import unittest
import pytest

# Disable import-error b/c our libraries aren't loaded in jenkins
# pylint: disable=import-error,wrong-import-position
# place class in our python path
module_path = os.path.join('/'.join(os.path.realpath(__file__).split(os.path.sep)[:-1]), 'library')
sys.path.insert(0, module_path)
openshift_cert_expiry = pytest.importorskip("openshift_cert_expiry")


@pytest.mark.skip('Skipping all tests because of unresolved import errors')
class TestFakeOpenSSLClasses(unittest.TestCase):
    '''
     Test class for FakeOpenSSL classes
    '''

    def setUp(self):
        ''' setup method for other tests '''
        with open('test/system-node-m01.example.com.crt.txt', 'r') as fp:
            self.cert_string = fp.read()

        self.fake_cert = openshift_cert_expiry.FakeOpenSSLCertificate(self.cert_string)

        with open('test/master.server.crt.txt', 'r') as fp:
            self.cert_san_string = fp.read()

        self.fake_san_cert = openshift_cert_expiry.FakeOpenSSLCertificate(self.cert_san_string)

    def test_FakeOpenSSLCertificate_get_serial_number(self):
        """We can read the serial number from the cert"""
        self.assertEqual(11, self.fake_cert.get_serial_number())

    def test_FakeOpenSSLCertificate_get_notAfter(self):
        """We can read the cert expiry date"""
        expiry = self.fake_cert.get_notAfter()
        self.assertEqual('20190207181935Z', expiry)

    def test_FakeOpenSSLCertificate_get_sans(self):
        """We can read Subject Alt Names from a cert"""
        ext = self.fake_san_cert.get_extension(0)

        if ext.get_short_name() == 'subjectAltName':
            sans = str(ext)

        self.assertEqual('DNS:kubernetes, DNS:kubernetes.default, DNS:kubernetes.default.svc, DNS:kubernetes.default.svc.cluster.local, DNS:m01.example.com, DNS:openshift, DNS:openshift.default, DNS:openshift.default.svc, DNS:openshift.default.svc.cluster.local, DNS:172.30.0.1, DNS:192.168.122.241, IP Address:172.30.0.1, IP Address:192.168.122.241', sans)

    def test_FakeOpenSSLCertificate_get_sans_no_sans(self):
        """We can tell when there are no Subject Alt Names in a cert"""
        with self.assertRaises(IndexError):
            self.fake_cert.get_extension(0)

    def test_FakeOpenSSLCertificate_get_subject(self):
        """We can read the Subject from a cert"""
        # Subject: O=system:nodes, CN=system:node:m01.example.com
        subject = self.fake_cert.get_subject()
        subjects = []
        for name, value in subject.get_components():
            subjects.append('{}={}'.format(name, value))

        self.assertEqual('O=system:nodes, CN=system:node:m01.example.com', ', '.join(subjects))

    def test_FakeOpenSSLCertificate_get_subject_san_cert(self):
        """We can read the Subject from a cert with sans"""
        # Subject: O=system:nodes, CN=system:node:m01.example.com
        subject = self.fake_san_cert.get_subject()
        subjects = []
        for name, value in subject.get_components():
            subjects.append('{}={}'.format(name, value))

        self.assertEqual('CN=172.30.0.1', ', '.join(subjects))


if __name__ == "__main__":
    unittest.main()
