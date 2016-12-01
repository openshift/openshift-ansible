import copy
import os
import sys

from ansible.errors import AnsibleError
from nose.tools import raises, assert_equal

sys.path = [os.path.abspath(os.path.dirname(__file__) + "/../lookup_plugins/")] + sys.path

from openshift_master_facts_default_predicates import LookupModule  # noqa: E402

DEFAULT_PREDICATES_1_1 = [
    {'name': 'PodFitsHostPorts'},
    {'name': 'PodFitsResources'},
    {'name': 'NoDiskConflict'},
    {'name': 'MatchNodeSelector'},
    {'name': 'Hostname'}
]

DEFAULT_PREDICATES_1_2 = [
    {'name': 'PodFitsHostPorts'},
    {'name': 'PodFitsResources'},
    {'name': 'NoDiskConflict'},
    {'name': 'NoVolumeZoneConflict'},
    {'name': 'MatchNodeSelector'},
    {'name': 'Hostname'},
    {'name': 'MaxEBSVolumeCount'},
    {'name': 'MaxGCEPDVolumeCount'}
]

DEFAULT_PREDICATES_1_3 = [
    {'name': 'NoDiskConflict'},
    {'name': 'NoVolumeZoneConflict'},
    {'name': 'MaxEBSVolumeCount'},
    {'name': 'MaxGCEPDVolumeCount'},
    {'name': 'GeneralPredicates'},
    {'name': 'PodToleratesNodeTaints'},
    {'name': 'CheckNodeMemoryPressure'}
]

DEFAULT_PREDICATES_1_4 = [
    {'name': 'NoDiskConflict'},
    {'name': 'NoVolumeZoneConflict'},
    {'name': 'MaxEBSVolumeCount'},
    {'name': 'MaxGCEPDVolumeCount'},
    {'name': 'GeneralPredicates'},
    {'name': 'PodToleratesNodeTaints'},
    {'name': 'CheckNodeMemoryPressure'},
    {'name': 'CheckNodeDiskPressure'},
    {'name': 'MatchInterPodAffinity'}
]

REGION_PREDICATE = {
    'name': 'Region',
    'argument': {
        'serviceAffinity': {
            'labels': ['region']
        }
    }
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

    def check_defaults(self, release, deployment_type, default_predicates,
                       regions_enabled, short_version):
        facts = copy.deepcopy(self.default_facts)
        if short_version:
            facts['openshift']['common']['short_version'] = release
        else:
            facts['openshift_release'] = release
        facts['openshift']['common']['deployment_type'] = deployment_type
        results = self.lookup.run(None, variables=facts,
                                  regions_enabled=regions_enabled)
        if regions_enabled:
            assert_equal(results, default_predicates + [REGION_PREDICATE])
        else:
            assert_equal(results, default_predicates)

    def test_openshift_release_defaults(self):
        test_vars = [
            ('1.1', 'origin', DEFAULT_PREDICATES_1_1),
            ('3.1', 'openshift-enterprise', DEFAULT_PREDICATES_1_1),
            ('1.2', 'origin', DEFAULT_PREDICATES_1_2),
            ('3.2', 'openshift-enterprise', DEFAULT_PREDICATES_1_2),
            ('1.3', 'origin', DEFAULT_PREDICATES_1_3),
            ('3.3', 'openshift-enterprise', DEFAULT_PREDICATES_1_3),
            ('1.4', 'origin', DEFAULT_PREDICATES_1_4),
            ('3.4', 'openshift-enterprise', DEFAULT_PREDICATES_1_4)
        ]

        for regions_enabled in (True, False):
            for release, deployment_type, default_predicates in test_vars:
                for prepend_v in (True, False):
                    if prepend_v:
                        release = 'v' + release
                yield self.check_defaults, release, deployment_type, default_predicates, regions_enabled, False

    def test_short_version_defaults(self):
        test_vars = [
            ('1.1', 'origin', DEFAULT_PREDICATES_1_1),
            ('3.1', 'openshift-enterprise', DEFAULT_PREDICATES_1_1),
            ('1.2', 'origin', DEFAULT_PREDICATES_1_2),
            ('3.2', 'openshift-enterprise', DEFAULT_PREDICATES_1_2),
            ('1.3', 'origin', DEFAULT_PREDICATES_1_3),
            ('3.3', 'openshift-enterprise', DEFAULT_PREDICATES_1_3),
            ('1.4', 'origin', DEFAULT_PREDICATES_1_4),
            ('3.4', 'openshift-enterprise', DEFAULT_PREDICATES_1_4)
        ]
        for regions_enabled in (True, False):
            for short_version, deployment_type, default_predicates in test_vars:
                yield self.check_defaults, short_version, deployment_type, default_predicates, regions_enabled, True

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
    def testMissingOpenShiftFacts(self):
        facts = {}
        self.lookup.run(None, variables=facts)

    @raises(AnsibleError)
    def testMissingMasterRole(self):
        facts = {'openshift': {}}
        self.lookup.run(None, variables=facts)

    def testPreExistingPredicates(self):
        facts = {
            'openshift': {
                'master': {
                    'scheduler_predicates': [
                        {'name': 'pred_a'},
                        {'name': 'pred_b'}
                    ]
                }
            }
        }
        result = self.lookup.run(None, variables=facts)
        assert_equal(result, facts['openshift']['master']['scheduler_predicates'])

    def testDefinedPredicates(self):
        facts = {
            'openshift': {'master': {}},
            'openshift_master_scheduler_predicates': [
                {'name': 'pred_a'},
                {'name': 'pred_b'}
            ]
        }
        result = self.lookup.run(None, variables=facts)
        assert_equal(result, facts['openshift_master_scheduler_predicates'])
