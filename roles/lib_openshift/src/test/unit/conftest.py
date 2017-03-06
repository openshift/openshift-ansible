import os

import pytest


USER_BIN_CLIENT = os.path.expanduser('~/bin/oc')
BINARY_LOOKUP_PARAMS = [
    {
        'id': 'not found',
        'binaries': ['oc'],
        'binary_expected': 'oc',
        'which_result': None,
        'path': ''
    },
    {
        'id': 'in path',
        'binaries': ['/usr/bin/oc'],
        'binary_expected': '/usr/bin/oc',
        'which_result': '/usr/bin/oc',
        'path': '/bin:/usr/bin'
    },
    {
        'id': '/usr/local/bin shadowed',
        'binaries': ['/usr/bin/oc', '/usr/local/bin/oc'],
        'binary_expected': '/usr/bin/oc',
        'which_result': '/usr/bin/oc',
        'path': '/bin:/usr/bin'
    },
    {
        'id': '/usr/local/bin fallback',
        'binaries': ['/usr/local/bin/oc'],
        'binary_expected': '/usr/local/bin/oc',
        'which_result': '/usr/local/bin/oc',
        'path': '/bin:/usr/bin'
    },
    {
        'id': '~/bin shadowed',
        'binaries': ['/usr/bin/oc', USER_BIN_CLIENT],
        'binary_expected': '/usr/bin/oc',
        'which_result': '/usr/bin/oc',
        'path': '/bin:/usr/bin'
    },
    {
        'id': '~/bin fallback',
        'binaries': [USER_BIN_CLIENT],
        'binary_expected': USER_BIN_CLIENT,
        'which_result': USER_BIN_CLIENT,
        'path': '/bin:/usr/bin'
    }
]
BINARY_LOOKUP_IDS = [param['id'] for param in BINARY_LOOKUP_PARAMS]


@pytest.fixture(ids=BINARY_LOOKUP_IDS, params=BINARY_LOOKUP_PARAMS)
def binary_lookup_test_data(request):
    return request.param
