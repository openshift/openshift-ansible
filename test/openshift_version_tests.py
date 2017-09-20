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

    # Static tests for legacy filters.
    legacy_gte_tests = [{'name': 'oo_version_gte_3_1_or_1_1',
                         'positive_openshift-enterprise_version': '3.2.0',
                         'negative_openshift-enterprise_version': '3.0.0',
                         'positive_origin_version': '1.2.0',
                         'negative_origin_version': '1.0.0'},
                        {'name': 'oo_version_gte_3_1_1_or_1_1_1',
                         'positive_openshift-enterprise_version': '3.2.0',
                         'negative_openshift-enterprise_version': '3.1.0',
                         'positive_origin_version': '1.2.0',
                         'negative_origin_version': '1.1.0'},
                        {'name': 'oo_version_gte_3_2_or_1_2',
                         'positive_openshift-enterprise_version': '3.3.0',
                         'negative_openshift-enterprise_version': '3.1.0',
                         'positive_origin_version': '1.3.0',
                         'negative_origin_version': '1.1.0'},
                        {'name': 'oo_version_gte_3_3_or_1_3',
                         'positive_openshift-enterprise_version': '3.4.0',
                         'negative_openshift-enterprise_version': '3.2.0',
                         'positive_origin_version': '1.4.0',
                         'negative_origin_version': '1.2.0'},
                        {'name': 'oo_version_gte_3_4_or_1_4',
                         'positive_openshift-enterprise_version': '3.5.0',
                         'negative_openshift-enterprise_version': '3.3.0',
                         'positive_origin_version': '1.5.0',
                         'negative_origin_version': '1.3.0'},
                        {'name': 'oo_version_gte_3_5_or_1_5',
                         'positive_openshift-enterprise_version': '3.6.0',
                         'negative_openshift-enterprise_version': '3.4.0',
                         'positive_origin_version': '3.6.0',
                         'negative_origin_version': '1.4.0'}]

    def test_legacy_gte_filters(self):
        for test in self.legacy_gte_tests:
            for deployment_type in ['openshift-enterprise', 'origin']:
                # Test negative case per deployment_type
                self.assertFalse(
                    self.openshift_version_filters._filters[test['name']](
                        test["negative_{}_version".format(deployment_type)], deployment_type))
                # Test positive case per deployment_type
                self.assertTrue(
                    self.openshift_version_filters._filters[test['name']](
                        test["positive_{}_version".format(deployment_type)], deployment_type))

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
