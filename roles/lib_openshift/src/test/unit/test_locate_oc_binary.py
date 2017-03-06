'''
 Unit tests for oc secret add
'''
from __future__ import absolute_import, print_function

import os

import pytest

USER_BIN_CLIENT = os.path.expanduser('~/bin/oc')
BINARY_LOOKUP_PARAMS = [
    {
        'id': 'not found',
        'binaries': ['oc'],
        'binary_expected': 'oc',
        'path': ''
    },
    {
        'id': 'in path',
        'binaries': ['/usr/bin/oc'],
        'binary_expected': '/usr/bin/oc',
        'path': '/bin:/usr/bin'
    },
    {
        'id': '/usr/local/bin shadowed',
        'binaries': ['/usr/bin/oc', '/usr/local/bin/oc'],
        'binary_expected': '/usr/bin/oc',
        'path': '/bin:/usr/bin'
    },
    {
        'id': '/usr/local/bin fallback',
        'binaries': ['/usr/local/bin/oc'],
        'binary_expected': '/usr/local/bin/oc',
        'path': '/bin:/usr/bin'
    },
    {
        'id': '~/bin shadowed',
        'binaries': ['/usr/bin/oc', USER_BIN_CLIENT],
        'binary_expected': '/usr/bin/oc',
        'path': '/bin:/usr/bin'
    },
    {
        'id': '~/bin fallback',
        'binaries': [USER_BIN_CLIENT],
        'binary_expected': USER_BIN_CLIENT,
        'path': '/bin:/usr/bin'
    }
]
BINARY_LOOKUP_IDS = [param['id'] for param in BINARY_LOOKUP_PARAMS]


@pytest.fixture(params=BINARY_LOOKUP_PARAMS, ids=BINARY_LOOKUP_IDS)
def lookup_test_data(request):
    yield request.param


def test_binary_lookup(lookup_test_data, binary_lookup_module, mocker):
    path = lookup_test_data['path']
    binary_expected = lookup_test_data['binary_expected']
    binaries = lookup_test_data['binaries']

    mocker.patch('os.environ.get', side_effect=lambda _v, _d: path)
    mocker.patch('os.path.exists', side_effect=lambda f: f in binaries)
    mocker.patch('os.access', side_effect=lambda f, _: f in binaries)

    assert binary_lookup_module.locate_oc_binary() == binary_expected
