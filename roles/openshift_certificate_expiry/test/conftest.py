# pylint: disable=missing-docstring,invalid-name,redefined-outer-name
import pytest
from OpenSSL import crypto

# Parameter list for valid_cert fixture
VALID_CERTIFICATE_PARAMS = [
    {
        'short_name': 'client',
        'cn': 'client.example.com',
        'serial': 4,
        'uses': b'clientAuth',
        'dns': [],
        'ip': [],
    },
    {
        'short_name': 'server',
        'cn': 'server.example.com',
        'serial': 5,
        'uses': b'serverAuth',
        'dns': ['kubernetes', 'openshift'],
        'ip': ['10.0.0.1', '192.168.0.1']
    },
    {
        'short_name': 'combined',
        'cn': 'combined.example.com',
        # Verify that HUGE serials parse correctly.
        # Frobs PARSING_HEX_SERIAL in _parse_cert
        # See https://bugzilla.redhat.com/show_bug.cgi?id=1464240
        'serial': 14449739080294792594019643629255165375,
        'uses': b'clientAuth, serverAuth',
        'dns': ['etcd'],
        'ip': ['10.0.0.2', '192.168.0.2']
    }
]

# Extract the short_name from VALID_CERTIFICATE_PARAMS to provide
# friendly naming for the valid_cert fixture
VALID_CERTIFICATE_IDS = [param['short_name'] for param in VALID_CERTIFICATE_PARAMS]


@pytest.fixture(scope='session')
def ca(tmpdir_factory):
    ca_dir = tmpdir_factory.mktemp('ca')

    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    cert = crypto.X509()
    cert.set_version(3)
    cert.set_serial_number(1)
    cert.get_subject().commonName = 'test-signer'
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(24 * 60 * 60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(key)
    cert.add_extensions([
        crypto.X509Extension(b'basicConstraints', True, b'CA:TRUE, pathlen:0'),
        crypto.X509Extension(b'keyUsage', True,
                             b'digitalSignature, keyEncipherment, keyCertSign, cRLSign'),
        crypto.X509Extension(b'subjectKeyIdentifier', False, b'hash', subject=cert)
    ])
    cert.add_extensions([
        crypto.X509Extension(b'authorityKeyIdentifier', False, b'keyid:always', issuer=cert)
    ])
    cert.sign(key, 'sha256')

    return {
        'dir': ca_dir,
        'key': key,
        'cert': cert,
    }


@pytest.fixture(scope='session',
                ids=VALID_CERTIFICATE_IDS,
                params=VALID_CERTIFICATE_PARAMS)
def valid_cert(request, ca):
    common_name = request.param['cn']

    key = crypto.PKey()
    key.generate_key(crypto.TYPE_RSA, 2048)

    cert = crypto.X509()
    cert.set_serial_number(request.param['serial'])
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(24 * 60 * 60)
    cert.set_issuer(ca['cert'].get_subject())
    cert.set_pubkey(key)
    cert.set_version(3)
    cert.get_subject().commonName = common_name
    cert.add_extensions([
        crypto.X509Extension(b'basicConstraints', True, b'CA:FALSE'),
        crypto.X509Extension(b'keyUsage', True, b'digitalSignature, keyEncipherment'),
        crypto.X509Extension(b'extendedKeyUsage', False, request.param['uses']),
    ])

    if request.param['dns'] or request.param['ip']:
        san_list = ['DNS:{}'.format(common_name)]
        san_list.extend(['DNS:{}'.format(x) for x in request.param['dns']])
        san_list.extend(['IP:{}'.format(x) for x in request.param['ip']])

        cert.add_extensions([
            crypto.X509Extension(b'subjectAltName', False, ', '.join(san_list).encode('utf8'))
        ])
    cert.sign(ca['key'], 'sha256')

    cert_contents = crypto.dump_certificate(crypto.FILETYPE_PEM, cert)
    cert_file = ca['dir'].join('{}.crt'.format(common_name))
    cert_file.write_binary(cert_contents)

    return {
        'common_name': common_name,
        'serial': request.param['serial'],
        'dns': request.param['dns'],
        'ip': request.param['ip'],
        'uses': request.param['uses'],
        'cert_file': cert_file,
        'cert': cert
    }
