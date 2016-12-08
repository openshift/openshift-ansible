import copy
import os
import sys

from ansible.errors import AnsibleError
from nose.tools import raises, assert_equal

sys.path = [os.path.abspath(os.path.dirname(__file__) + "/../lookup_plugins/")] + sys.path

from openshift_master_facts_default_priorities import LookupModule  # noqa: E402

DEFAULT_PRIORITIES_1_1 = [
    {'name': 'LeastRequestedPriority', 'weight': 1},
    {'name': 'BalancedResourceAllocation', 'weight': 1},
    {'name': 'SelectorSpreadPriority', 'weight': 1}
]

DEFAULT_PRIORITIES_1_2 = [
    {'name': 'LeastRequestedPriority', 'weight': 1},
    {'name': 'BalancedResourceAllocation', 'weight': 1},
    {'name': 'SelectorSpreadPriority', 'weight': 1},
    {'name': 'NodeAffinityPriority', 'weight': 1}
]

DEFAULT_PRIORITIES_1_3 = [
    {'name': 'LeastRequestedPriority', 'weight': 1},
    {'name': 'BalancedResourceAllocation', 'weight': 1},
    {'name': 'SelectorSpreadPriority', 'weight': 1},
    {'name': 'NodeAffinityPriority', 'weight': 1},
    {'name': 'TaintTolerationPriority', 'weight': 1}
]

DEFAULT_PRIORITIES_1_4 = [
    {'name': 'LeastRequestedPriority', 'weight': 1},
    {'name': 'BalancedResourceAllocation', 'weight': 1},
    {'name': 'SelectorSpreadPriority', 'weight': 1},
    {'name': 'NodePreferAvoidPodsPriority', 'weight': 10000},
    {'name': 'NodeAffinityPriority', 'weight': 1},
    {'name': 'TaintTolerationPriority', 'weight': 1},
    {'name': 'InterPodAffinityPriority', 'weight': 1}
]

ZONE_PRIORITY = {
    'name': 'Zone',
    'argument': {
        'serviceAntiAffinity': {
            'label': 'zone'
        }
    },
    'weight': 2
}

TEST_VARS = [
    ('1.1', 'origin', DEFAULT_PRIORITIES_1_1),
    ('3.1', 'openshift-enterprise', DEFAULT_PRIORITIES_1_1),
    ('1.2', 'origin', DEFAULT_PRIORITIES_1_2),
    ('3.2', 'openshift-enterprise', DEFAULT_PRIORITIES_1_2),
    ('1.3', 'origin', DEFAULT_PRIORITIES_1_3),
    ('3.3', 'openshift-enterprise', DEFAULT_PRIORITIES_1_3),
    ('1.4', 'origin', DEFAULT_PRIORITIES_1_4),
    ('3.4', 'openshift-enterprise', DEFAULT_PRIORITIES_1_4)
]


class TestOpenShiftMasterFactsDefaultPredicates(object):
    def setUp(self):
        self.lookup = LookupModule()
        self.default_facts = {
            'openshift': {
                'common': {}
            }
        }

    @raises(AnsibleError)
    def test_missing_short_version_and_missing_openshift_release(self):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['deployment_type'] = 'origin'
        self.lookup.run(None, variables=facts)

    def check_defaults_short_version(self, release, deployment_type,
                                     default_priorities, zones_enabled):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['short_version'] = release
        facts['openshift']['common']['deployment_type'] = deployment_type
        results = self.lookup.run(None, variables=facts, zones_enabled=zones_enabled)
        if zones_enabled:
            assert_equal(results, default_priorities + [ZONE_PRIORITY])
        else:
            assert_equal(results, default_priorities)

    def check_defaults_short_version_kwarg(self, release, deployment_type,
                                           default_priorities, zones_enabled):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['deployment_type'] = deployment_type
        results = self.lookup.run(None, variables=facts,
                                  zones_enabled=zones_enabled,
                                  short_version=release)
        if zones_enabled:
            assert_equal(results, default_priorities + [ZONE_PRIORITY])
        else:
            assert_equal(results, default_priorities)

    def check_defaults_deployment_type_kwarg(self, release, deployment_type,
                                             default_priorities, zones_enabled):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['short_version'] = release
        results = self.lookup.run(None, variables=facts,
                                  zones_enabled=zones_enabled,
                                  deployment_type=deployment_type)
        if zones_enabled:
            assert_equal(results, default_priorities + [ZONE_PRIORITY])
        else:
            assert_equal(results, default_priorities)

    def check_defaults_only_kwargs(self, release, deployment_type,
                                   default_priorities, zones_enabled):
        facts = copy.deepcopy(self.default_facts)
        results = self.lookup.run(None, variables=facts,
                                  zones_enabled=zones_enabled,
                                  short_version=release,
                                  deployment_type=deployment_type)
        if zones_enabled:
            assert_equal(results, default_priorities + [ZONE_PRIORITY])
        else:
            assert_equal(results, default_priorities)

    def check_defaults_release(self, release, deployment_type, default_priorities,
                               zones_enabled):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift_release'] = release
        facts['openshift']['common']['deployment_type'] = deployment_type
        results = self.lookup.run(None, variables=facts, zones_enabled=zones_enabled)
        if zones_enabled:
            assert_equal(results, default_priorities + [ZONE_PRIORITY])
        else:
            assert_equal(results, default_priorities)

    def check_defaults_version(self, release, deployment_type, default_priorities,
                               zones_enabled):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift_version'] = release
        facts['openshift']['common']['deployment_type'] = deployment_type
        results = self.lookup.run(None, variables=facts, zones_enabled=zones_enabled)
        if zones_enabled:
            assert_equal(results, default_priorities + [ZONE_PRIORITY])
        else:
            assert_equal(results, default_priorities)

    def check_defaults_override_vars(self, release, deployment_type,
                                     default_priorities, zones_enabled,
                                     extra_facts=None):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['short_version'] = release
        facts['openshift']['common']['deployment_type'] = deployment_type
        if extra_facts is not None:
            for fact in extra_facts:
                facts[fact] = extra_facts[fact]
        results = self.lookup.run(None, variables=facts,
                                  zones_enabled=zones_enabled,
                                  return_set_vars=False)
        if zones_enabled:
            assert_equal(results, default_priorities + [ZONE_PRIORITY])
        else:
            assert_equal(results, default_priorities)

    def test_openshift_version(self):
        for zones_enabled in (True, False):
            for release, deployment_type, default_priorities in TEST_VARS:
                release = release + '.1'
                yield self.check_defaults_version, release, deployment_type, default_priorities, zones_enabled

    def test_v_release_defaults(self):
        for zones_enabled in (True, False):
            for release, deployment_type, default_priorities in TEST_VARS:
                release = 'v' + release
                yield self.check_defaults_release, release, deployment_type, default_priorities, zones_enabled

    def test_release_defaults(self):
        for zones_enabled in (True, False):
            for release, deployment_type, default_priorities in TEST_VARS:
                yield self.check_defaults_release, release, deployment_type, default_priorities, zones_enabled

    def test_short_version_defaults(self):
        for zones_enabled in (True, False):
            for short_version, deployment_type, default_priorities in TEST_VARS:
                yield self.check_defaults_short_version, short_version, deployment_type, default_priorities, zones_enabled

    def test_only_kwargs(self):
        for zones_enabled in (True, False):
            for short_version, deployment_type, default_priorities in TEST_VARS:
                yield self.check_defaults_only_kwargs, short_version, deployment_type, default_priorities, zones_enabled

    def test_deployment_type_kwarg(self):
        for zones_enabled in (True, False):
            for short_version, deployment_type, default_priorities in TEST_VARS:
                yield self.check_defaults_deployment_type_kwarg, short_version, deployment_type, default_priorities, zones_enabled

    def test_release_kwarg(self):
        for zones_enabled in (True, False):
            for short_version, deployment_type, default_priorities in TEST_VARS:
                yield self.check_defaults_short_version_kwarg, short_version, deployment_type, default_priorities, zones_enabled

    def test_trunc_openshift_release(self):
        for release, deployment_type, default_priorities in TEST_VARS:
            release = release + '.1'
            yield self.check_defaults_release, release, deployment_type, default_priorities, False

    @raises(AnsibleError)
    def test_unknown_origin_version(self):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['short_version'] = '0.1'
        facts['openshift']['common']['deployment_type'] = 'origin'
        self.lookup.run(None, variables=facts)

    @raises(AnsibleError)
    def test_unknown_ocp_version(self):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['short_version'] = '0.1'
        facts['openshift']['common']['deployment_type'] = 'openshift-enterprise'
        self.lookup.run(None, variables=facts)

    @raises(AnsibleError)
    def test_unknown_deployment_types(self):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['short_version'] = '1.1'
        facts['openshift']['common']['deployment_type'] = 'bogus'
        self.lookup.run(None, variables=facts)

    @raises(AnsibleError)
    def test_missing_deployment_type(self):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['short_version'] = '10.10'
        self.lookup.run(None, variables=facts)

    @raises(AnsibleError)
    def test_missing_openshift_facts(self):
        facts = {}
        self.lookup.run(None, variables=facts)
