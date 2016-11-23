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


class TestOpenShiftMasterFactsDefaultPredicates(object):
    def setUp(self):
        self.lookup = LookupModule()
        self.default_facts = {
            'openshift': {
                'master': {},
                'common': {}
            }
        }

    @raises(AnsibleError)
    def test_missing_short_version_and_missing_openshift_release(self):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['deployment_type'] = 'origin'
        self.lookup.run(None, variables=facts)

    def check_defaults(self, release, deployment_type, default_priorities,
                       zones_enabled, short_version):
        facts = copy.deepcopy(self.default_facts)
        if short_version:
            facts['openshift']['common']['short_version'] = release
        else:
            facts['openshift_release'] = release
        facts['openshift']['common']['deployment_type'] = deployment_type
        results = self.lookup.run(None, variables=facts, zones_enabled=zones_enabled)
        if zones_enabled:
            assert_equal(results, default_priorities + [ZONE_PRIORITY])
        else:
            assert_equal(results, default_priorities)

    def test_openshift_release_defaults(self):
        test_vars = [
            ('1.1', 'origin', DEFAULT_PRIORITIES_1_1),
            ('3.1', 'openshift-enterprise', DEFAULT_PRIORITIES_1_1),
            ('1.2', 'origin', DEFAULT_PRIORITIES_1_2),
            ('3.2', 'openshift-enterprise', DEFAULT_PRIORITIES_1_2),
            ('1.3', 'origin', DEFAULT_PRIORITIES_1_3),
            ('3.3', 'openshift-enterprise', DEFAULT_PRIORITIES_1_3),
            ('1.4', 'origin', DEFAULT_PRIORITIES_1_4),
            ('3.4', 'openshift-enterprise', DEFAULT_PRIORITIES_1_4)
        ]

        for zones_enabled in (True, False):
            for release, deployment_type, default_priorities in test_vars:
                for prepend_v in (True, False):
                    if prepend_v:
                        release = 'v' + release
                yield self.check_defaults, release, deployment_type, default_priorities, zones_enabled, False

    def test_short_version_defaults(self):
        test_vars = [
            ('1.1', 'origin', DEFAULT_PRIORITIES_1_1),
            ('3.1', 'openshift-enterprise', DEFAULT_PRIORITIES_1_1),
            ('1.2', 'origin', DEFAULT_PRIORITIES_1_2),
            ('3.2', 'openshift-enterprise', DEFAULT_PRIORITIES_1_2),
            ('1.3', 'origin', DEFAULT_PRIORITIES_1_3),
            ('3.3', 'openshift-enterprise', DEFAULT_PRIORITIES_1_3),
            ('1.4', 'origin', DEFAULT_PRIORITIES_1_4),
            ('3.4', 'openshift-enterprise', DEFAULT_PRIORITIES_1_4)
        ]
        for zones_enabled in (True, False):
            for short_version, deployment_type, default_priorities in test_vars:
                yield self.check_defaults, short_version, deployment_type, default_priorities, zones_enabled, True

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

    @raises(AnsibleError)
    def test_missing_master_role(self):
        facts = {'openshift': {}}
        self.lookup.run(None, variables=facts)

    def test_pre_existing_priorities(self):
        facts = {
            'openshift': {
                'master': {
                    'scheduler_priorities': [
                        {'name': 'pri_a', 'weight': 1},
                        {'name': 'pri_b', 'weight': 1}
                    ]
                }
            }
        }
        result = self.lookup.run(None, variables=facts)
        assert_equal(result, facts['openshift']['master']['scheduler_priorities'])

    def testDefinedPredicates(self):
        facts = {
            'openshift': {'master': {}},
            'openshift_master_scheduler_priorities': [
                {'name': 'pri_a', 'weight': 1},
                {'name': 'pri_b', 'weight': 1}
            ]
        }
        result = self.lookup.run(None, variables=facts)
        assert_equal(result, facts['openshift_master_scheduler_priorities'])
