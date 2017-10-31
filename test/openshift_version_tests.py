""" Tests for the openshift_version Ansible filter module. """
# pylint: disable=missing-docstring,invalid-name

import os
import sys
import unittest

sys.path = [os.path.abspath(os.path.dirname(__file__) + "/../filter_plugins/")] + sys.path

# pylint: disable=import-error
import openshift_version  # noqa: E402


class OpenShiftVersionTests(unittest.TestCase):

    openshift_version_filters = openshift_version.FilterModule()

    def test_gte_filters(self):
        for major, minor_start, minor_end in self.openshift_version_filters.versions:
            for minor in range(minor_start, minor_end):
                # Test positive case
                self.assertTrue(
                    self.openshift_version_filters._filters["oo_version_gte_{}_{}".format(major, minor)](
                        "{}.{}".format(major, minor + 1)))
                # Test negative case
                self.assertFalse(
                    self.openshift_version_filters._filters["oo_version_gte_{}_{}".format(major, minor)](
                        "{}.{}".format(major, minor)))

    def test_get_filters(self):
        self.assertTrue(
            self.openshift_version_filters.filters() == self.openshift_version_filters._filters)
