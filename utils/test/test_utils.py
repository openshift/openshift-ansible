"""
Unittests for ooinstall utils.
"""

import unittest
import copy
import mock

import six

from ooinstall.utils import debug_env, is_valid_hostname


class TestUtils(unittest.TestCase):
    """
    Parent unittest TestCase.
    """

    def setUp(self):
        self.debug_all_params = {
            'OPENSHIFT_FOO': 'bar',
            'ANSIBLE_FOO': 'bar',
            'OO_FOO': 'bar'
        }

        self.expected = [
            mock.call('ANSIBLE_FOO: bar'),
            mock.call('OPENSHIFT_FOO: bar'),
            mock.call('OO_FOO: bar'),
        ]


    ######################################################################
    # Validate ooinstall.utils.debug_env functionality

    def test_utils_debug_env_all_debugged(self):
        """Verify debug_env debugs specific env variables"""

        with mock.patch('ooinstall.utils.installer_log') as _il:
            debug_env(self.debug_all_params)

            # Debug was called for each item we expect
            self.assertEqual(
                len(self.debug_all_params),
                _il.debug.call_count)

            # Each item we expect was logged
            six.assertCountEqual(
                self,
                self.expected,
                _il.debug.call_args_list)

    def test_utils_debug_env_some_debugged(self):
        """Verify debug_env skips non-wanted env variables"""
        debug_some_params = copy.deepcopy(self.debug_all_params)
        # This will not be logged by debug_env
        debug_some_params['MG_FRBBR'] = "SKIPPED"

        with mock.patch('ooinstall.utils.installer_log') as _il:
            debug_env(debug_some_params)

            # The actual number of debug calls was less than the
            # number of items passed to debug_env
            self.assertLess(
                _il.debug.call_count,
                len(debug_some_params))

            six.assertCountEqual(
                self,
                self.expected,
                _il.debug.call_args_list)

    ######################################################################
    def test_utils_is_valid_hostname_invalid(self):
        """Verify is_valid_hostname can detect None or too-long hostnames"""
        # A hostname that's empty, None, or more than 255 chars is invalid
        empty_hostname = ''
        res = is_valid_hostname(empty_hostname)
        self.assertFalse(res)

        none_hostname = None
        res = is_valid_hostname(none_hostname)
        self.assertFalse(res)

        too_long_hostname = "a" * 256
        res = is_valid_hostname(too_long_hostname)
        self.assertFalse(res)

    def test_utils_is_valid_hostname_ends_with_dot(self):
        """Verify is_valid_hostname can parse hostnames with trailing periods"""
        hostname = "foo.example.com."
        res = is_valid_hostname(hostname)
        self.assertTrue(res)

    def test_utils_is_valid_hostname_normal_hostname(self):
        """Verify is_valid_hostname can parse regular hostnames"""
        hostname = "foo.example.com"
        res = is_valid_hostname(hostname)
        self.assertTrue(res)
