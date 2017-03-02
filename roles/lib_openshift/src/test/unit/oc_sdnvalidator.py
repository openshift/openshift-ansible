#!/usr/bin/env python2
'''
 Unit tests for oc sdnvalidator
'''
# To run
# ./oc_sdnvalidator.py
#
# ....
# ----------------------------------------------------------------------
# Ran 4 tests in 0.002s
#
# OK

import os
import sys
import unittest
import mock

# Removing invalid variable names for tests so that I can
# keep them brief
# pylint: disable=invalid-name,no-name-in-module
# Disable import-error b/c our libraries aren't loaded in jenkins
# pylint: disable=import-error
# place class in our python path
module_path = os.path.join('/'.join(os.path.realpath(__file__).split('/')[:-4]), 'library')  # noqa: E501
sys.path.insert(0, module_path)
from oc_sdnvalidator import OCSDNValidator  # noqa: E402


class OCSDNValidatorTest(unittest.TestCase):
    '''
     Test class for OCSDNValidator
    '''

    @mock.patch('oc_sdnvalidator.Utils.create_tmpfile_copy')
    @mock.patch('oc_sdnvalidator.OCSDNValidator._run')
    def test_no_data(self, mock_cmd, mock_tmpfile_copy):
        ''' Testing when both SDN objects are empty '''

        # Arrange

        # run_ansible input parameters
        params = {
            'kubeconfig': '/etc/origin/master/admin.kubeconfig',
        }

        empty = '''{
    "apiVersion": "v1",
    "items": [],
    "kind": "List",
    "metadata": {},
    "resourceVersion": "",
    "selfLink": ""
}'''

        # Return values of our mocked function call. These get returned once per call.
        mock_cmd.side_effect = [
            # First call to mock
            (0, empty, ''),

            # Second call to mock
            (0, empty, ''),
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mocked_kubeconfig',
        ]

        # Act
        results = OCSDNValidator.run_ansible(params)

        # Assert
        self.assertNotIn('failed', results)
        self.assertEqual(results['msg'], 'All SDN objects are valid.')

        # Making sure our mock was called as we expected
        mock_cmd.assert_has_calls([
            mock.call(['oc', '-n', 'default', 'get', 'hostsubnet', '-o', 'json'], None),
            mock.call(['oc', '-n', 'default', 'get', 'netnamespace', '-o', 'json'], None),
        ])

    @mock.patch('oc_sdnvalidator.Utils.create_tmpfile_copy')
    @mock.patch('oc_sdnvalidator.OCSDNValidator._run')
    def test_error_code(self, mock_cmd, mock_tmpfile_copy):
        ''' Testing when both we fail to get SDN objects '''

        # Arrange

        # run_ansible input parameters
        params = {
            'kubeconfig': '/etc/origin/master/admin.kubeconfig',
        }

        # Return values of our mocked function call. These get returned once per call.
        mock_cmd.side_effect = [
            # First call to mock
            (1, '', 'Error.'),
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mocked_kubeconfig',
        ]

        error_results = {
            'returncode': 1,
            'stderr': 'Error.',
            'stdout': '',
            'cmd': 'oc -n default get hostsubnet -o json',
            'results': [{}]
        }

        # Act
        results = OCSDNValidator.run_ansible(params)

        # Assert
        self.assertTrue(results['failed'])
        self.assertEqual(results['msg'], 'Failed to GET hostsubnet.')
        self.assertEqual(results['state'], 'list')
        self.assertEqual(results['results'], error_results)

        # Making sure our mock was called as we expected
        mock_cmd.assert_has_calls([
            mock.call(['oc', '-n', 'default', 'get', 'hostsubnet', '-o', 'json'], None),
        ])

    @mock.patch('oc_sdnvalidator.Utils.create_tmpfile_copy')
    @mock.patch('oc_sdnvalidator.OCSDNValidator._run')
    def test_valid_both(self, mock_cmd, mock_tmpfile_copy):
        ''' Testing when both SDN objects are valid '''

        # Arrange

        # run_ansible input parameters
        params = {
            'kubeconfig': '/etc/origin/master/admin.kubeconfig',
        }

        valid_hostsubnet = '''{
    "apiVersion": "v1",
    "items": [
        {
            "apiVersion": "v1",
            "host": "bar0",
            "hostIP": "1.1.1.1",
            "kind": "HostSubnet",
            "metadata": {
                "creationTimestamp": "2017-02-16T18:47:09Z",
                "name": "bar0",
                "namespace": "",
                "resourceVersion": "986",
                "selfLink": "/oapi/v1/hostsubnetsbar0",
                "uid": "528dbb41-f478-11e6-aae0-507b9dac97ff"
            },
            "subnet": "1.1.0.0/24"
        },
        {
            "apiVersion": "v1",
            "host": "bar1",
            "hostIP": "1.1.1.1",
            "kind": "HostSubnet",
            "metadata": {
                "creationTimestamp": "2017-02-16T18:47:18Z",
                "name": "bar1",
                "namespace": "",
                "resourceVersion": "988",
                "selfLink": "/oapi/v1/hostsubnetsbar1",
                "uid": "57710d84-f478-11e6-aae0-507b9dac97ff"
            },
            "subnet": "1.1.0.0/24"
        },
        {
            "apiVersion": "v1",
            "host": "bar2",
            "hostIP": "1.1.1.1",
            "kind": "HostSubnet",
            "metadata": {
                "creationTimestamp": "2017-02-16T18:47:26Z",
                "name": "bar2",
                "namespace": "",
                "resourceVersion": "991",
                "selfLink": "/oapi/v1/hostsubnetsbar2",
                "uid": "5c59a28c-f478-11e6-aae0-507b9dac97ff"
            },
            "subnet": "1.1.0.0/24"
        }
    ],
    "kind": "List",
    "metadata": {},
    "resourceVersion": "",
    "selfLink": ""
    }'''

        valid_netnamespace = '''{
    "apiVersion": "v1",
    "items": [
        {
            "apiVersion": "v1",
            "kind": "NetNamespace",
            "metadata": {
                "creationTimestamp": "2017-02-16T18:45:16Z",
                "name": "foo0",
                "namespace": "",
                "resourceVersion": "959",
                "selfLink": "/oapi/v1/netnamespacesfoo0",
                "uid": "0f1c85b2-f478-11e6-aae0-507b9dac97ff"
            },
            "netid": 100,
            "netname": "foo0"
        },
        {
            "apiVersion": "v1",
            "kind": "NetNamespace",
            "metadata": {
                "creationTimestamp": "2017-02-16T18:45:26Z",
                "name": "foo1",
                "namespace": "",
                "resourceVersion": "962",
                "selfLink": "/oapi/v1/netnamespacesfoo1",
                "uid": "14effa0d-f478-11e6-aae0-507b9dac97ff"
            },
            "netid": 100,
            "netname": "foo1"
        },
        {
            "apiVersion": "v1",
            "kind": "NetNamespace",
            "metadata": {
                "creationTimestamp": "2017-02-16T18:45:36Z",
                "name": "foo2",
                "namespace": "",
                "resourceVersion": "965",
                "selfLink": "/oapi/v1/netnamespacesfoo2",
                "uid": "1aabdf84-f478-11e6-aae0-507b9dac97ff"
            },
            "netid": 100,
            "netname": "foo2"
        }
    ],
    "kind": "List",
    "metadata": {},
    "resourceVersion": "",
    "selfLink": ""
    }'''

        # Return values of our mocked function call. These get returned once per call.
        mock_cmd.side_effect = [
            # First call to mock
            (0, valid_hostsubnet, ''),

            # Second call to mock
            (0, valid_netnamespace, ''),
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mocked_kubeconfig',
        ]

        # Act
        results = OCSDNValidator.run_ansible(params)

        # Assert
        self.assertNotIn('failed', results)
        self.assertEqual(results['msg'], 'All SDN objects are valid.')

        # Making sure our mock was called as we expected
        mock_cmd.assert_has_calls([
            mock.call(['oc', '-n', 'default', 'get', 'hostsubnet', '-o', 'json'], None),
            mock.call(['oc', '-n', 'default', 'get', 'netnamespace', '-o', 'json'], None),
        ])

    @mock.patch('oc_sdnvalidator.Utils.create_tmpfile_copy')
    @mock.patch('oc_sdnvalidator.OCSDNValidator._run')
    def test_invalid_both(self, mock_cmd, mock_tmpfile_copy):
        ''' Testing when both SDN objects are invalid '''

        # Arrange

        # run_ansible input parameters
        params = {
            'kubeconfig': '/etc/origin/master/admin.kubeconfig',
        }

        invalid_hostsubnet = '''{
    "apiVersion": "v1",
    "items": [
        {
            "apiVersion": "v1",
            "host": "bar0",
            "hostIP": "1.1.1.1",
            "kind": "HostSubnet",
            "metadata": {
                "creationTimestamp": "2017-02-16T18:47:09Z",
                "name": "bar0",
                "namespace": "",
                "resourceVersion": "986",
                "selfLink": "/oapi/v1/hostsubnetsbar0",
                "uid": "528dbb41-f478-11e6-aae0-507b9dac97ff"
            },
            "subnet": "1.1.0.0/24"
        },
        {
            "apiVersion": "v1",
            "host": "bar1",
            "hostIP": "1.1.1.1",
            "kind": "HostSubnet",
            "metadata": {
                "creationTimestamp": "2017-02-16T18:47:18Z",
                "name": "bar1",
                "namespace": "",
                "resourceVersion": "988",
                "selfLink": "/oapi/v1/hostsubnetsbar1",
                "uid": "57710d84-f478-11e6-aae0-507b9dac97ff"
            },
            "subnet": "1.1.0.0/24"
        },
        {
            "apiVersion": "v1",
            "host": "bar2",
            "hostIP": "1.1.1.1",
            "kind": "HostSubnet",
            "metadata": {
                "creationTimestamp": "2017-02-16T18:47:26Z",
                "name": "bar2",
                "namespace": "",
                "resourceVersion": "991",
                "selfLink": "/oapi/v1/hostsubnetsbar2",
                "uid": "5c59a28c-f478-11e6-aae0-507b9dac97ff"
            },
            "subnet": "1.1.0.0/24"
        },
        {
            "apiVersion": "v1",
            "host": "baz1",
            "hostIP": "1.1.1.1",
            "kind": "HostSubnet",
            "metadata": {
                "creationTimestamp": "2017-02-16T18:47:49Z",
                "name": "baz0",
                "namespace": "",
                "resourceVersion": "996",
                "selfLink": "/oapi/v1/hostsubnetsbaz0",
                "uid": "69f75f87-f478-11e6-aae0-507b9dac97ff"
            },
            "subnet": "1.1.0.0/24"
        }
    ],
    "kind": "List",
    "metadata": {},
    "resourceVersion": "",
    "selfLink": ""
}'''

        invalid_netnamespace = '''{
    "apiVersion": "v1",
    "items": [
        {
            "apiVersion": "v1",
            "kind": "NetNamespace",
            "metadata": {
                "creationTimestamp": "2017-02-16T18:45:52Z",
                "name": "bar0",
                "namespace": "",
                "resourceVersion": "969",
                "selfLink": "/oapi/v1/netnamespacesbar0",
                "uid": "245d416e-f478-11e6-aae0-507b9dac97ff"
            },
            "netid": 100,
            "netname": "bar1"
        },
        {
            "apiVersion": "v1",
            "kind": "NetNamespace",
            "metadata": {
                "creationTimestamp": "2017-02-16T18:45:16Z",
                "name": "foo0",
                "namespace": "",
                "resourceVersion": "959",
                "selfLink": "/oapi/v1/netnamespacesfoo0",
                "uid": "0f1c85b2-f478-11e6-aae0-507b9dac97ff"
            },
            "netid": 100,
            "netname": "foo0"
        },
        {
            "apiVersion": "v1",
            "kind": "NetNamespace",
            "metadata": {
                "creationTimestamp": "2017-02-16T18:45:26Z",
                "name": "foo1",
                "namespace": "",
                "resourceVersion": "962",
                "selfLink": "/oapi/v1/netnamespacesfoo1",
                "uid": "14effa0d-f478-11e6-aae0-507b9dac97ff"
            },
            "netid": 100,
            "netname": "foo1"
        },
        {
            "apiVersion": "v1",
            "kind": "NetNamespace",
            "metadata": {
                "creationTimestamp": "2017-02-16T18:45:36Z",
                "name": "foo2",
                "namespace": "",
                "resourceVersion": "965",
                "selfLink": "/oapi/v1/netnamespacesfoo2",
                "uid": "1aabdf84-f478-11e6-aae0-507b9dac97ff"
            },
            "netid": 100,
            "netname": "foo2"
        }
    ],
    "kind": "List",
    "metadata": {},
    "resourceVersion": "",
    "selfLink": ""
}'''

        invalid_results = {
            'hostsubnets where metadata.name != host': [{
                'apiVersion': 'v1',
                'host': 'baz1',
                'hostIP': '1.1.1.1',
                'kind': 'HostSubnet',
                'metadata': {
                    'creationTimestamp': '2017-02-16T18:47:49Z',
                    'name': 'baz0',
                    'namespace': '',
                    'resourceVersion': '996',
                    'selfLink': '/oapi/v1/hostsubnetsbaz0',
                    'uid': '69f75f87-f478-11e6-aae0-507b9dac97ff'
                },
                'subnet': '1.1.0.0/24'
            }],
            'netnamespaces where metadata.name != netname': [{
                'apiVersion': 'v1',
                'kind': 'NetNamespace',
                'metadata': {
                    'creationTimestamp': '2017-02-16T18:45:52Z',
                    'name': 'bar0',
                    'namespace': '',
                    'resourceVersion': '969',
                    'selfLink': '/oapi/v1/netnamespacesbar0',
                    'uid': '245d416e-f478-11e6-aae0-507b9dac97ff'
                },
                'netid': 100,
                'netname': 'bar1'
            }],
        }

        # Return values of our mocked function call. These get returned once per call.
        mock_cmd.side_effect = [
            # First call to mock
            (0, invalid_hostsubnet, ''),

            # Second call to mock
            (0, invalid_netnamespace, ''),
        ]

        mock_tmpfile_copy.side_effect = [
            '/tmp/mocked_kubeconfig',
        ]

        # Act
        results = OCSDNValidator.run_ansible(params)

        # Assert
        self.assertTrue(results['failed'])
        self.assertEqual(results['msg'], 'All SDN objects are not valid.')
        self.assertEqual(results['state'], 'list')
        self.assertEqual(results['results'], invalid_results)

        # Making sure our mock was called as we expected
        mock_cmd.assert_has_calls([
            mock.call(['oc', '-n', 'default', 'get', 'hostsubnet', '-o', 'json'], None),
            mock.call(['oc', '-n', 'default', 'get', 'netnamespace', '-o', 'json'], None),
        ])


if __name__ == '__main__':
    unittest.main()
