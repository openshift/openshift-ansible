"""
Unittests for ooinstall utils.
"""

import unittest
import logging
import sys
import copy
from ooinstall.utils import debug_env
import mock


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

        # python 2.x has assertItemsEqual, python 3.x has assertCountEqual
        if sys.version_info.major > 3:
            self.assertItemsEqual = self.assertCountEqual

    ######################################################################
    # Validate ooinstall.utils.debug_env functionality

    def test_utils_debug_env_all_debugged(self):
        """Verify debug_env debugs specific env variables"""

        with mock.patch('ooinstall.utils.installer_log') as _il:
            debug_env(self.debug_all_params)
            print _il.debug.call_args_list

            # Debug was called for each item we expect
            self.assertEqual(
                len(self.debug_all_params),
                _il.debug.call_count)

            # Each item we expect was logged
            self.assertItemsEqual(
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

            self.assertItemsEqual(
                self.expected,
                _il.debug.call_args_list)
