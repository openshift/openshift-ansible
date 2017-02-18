import copy
import os
import sys

from nose.tools import assert_equal

sys.path.insert(1, os.path.join(os.path.dirname(__file__), os.pardir, "lookup_plugins"))

from openshift_master_facts_default_predicates import LookupModule  # noqa: E402

# Predicates ordered according to OpenShift Origin source:
# origin/vendor/k8s.io/kubernetes/plugin/pkg/scheduler/algorithmprovider/defaults/defaults.go

DEFAULT_PREDICATES_1_1 = [
    {'name': 'PodFitsHostPorts'},
    {'name': 'PodFitsResources'},
    {'name': 'NoDiskConflict'},
    {'name': 'MatchNodeSelector'},
]

DEFAULT_PREDICATES_1_2 = [
    {'name': 'PodFitsHostPorts'},
    {'name': 'PodFitsResources'},
    {'name': 'NoDiskConflict'},
    {'name': 'NoVolumeZoneConflict'},
    {'name': 'MatchNodeSelector'},
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

DEFAULT_PREDICATES_1_5 = [
    {'name': 'NoVolumeZoneConflict'},
    {'name': 'MaxEBSVolumeCount'},
    {'name': 'MaxGCEPDVolumeCount'},
    {'name': 'MatchInterPodAffinity'},
    {'name': 'NoDiskConflict'},
    {'name': 'GeneralPredicates'},
    {'name': 'PodToleratesNodeTaints'},
    {'name': 'CheckNodeMemoryPressure'},
    {'name': 'CheckNodeDiskPressure'},
]

REGION_PREDICATE = {
    'name': 'Region',
    'argument': {
        'serviceAffinity': {
            'labels': ['region']
        }
    }
}

TEST_VARS = [
    ('1.1', 'origin', DEFAULT_PREDICATES_1_1),
    ('3.1', 'openshift-enterprise', DEFAULT_PREDICATES_1_1),
    ('1.2', 'origin', DEFAULT_PREDICATES_1_2),
    ('3.2', 'openshift-enterprise', DEFAULT_PREDICATES_1_2),
    ('1.3', 'origin', DEFAULT_PREDICATES_1_3),
    ('3.3', 'openshift-enterprise', DEFAULT_PREDICATES_1_3),
    ('1.4', 'origin', DEFAULT_PREDICATES_1_4),
    ('3.4', 'openshift-enterprise', DEFAULT_PREDICATES_1_4),
    ('1.5', 'origin', DEFAULT_PREDICATES_1_5),
    ('3.5', 'openshift-enterprise', DEFAULT_PREDICATES_1_5),
    ('1.6', 'origin', DEFAULT_PREDICATES_1_5),
    ('3.6', 'openshift-enterprise', DEFAULT_PREDICATES_1_5),
]


class TestOpenShiftMasterFactsDefaultPredicates(object):
    def setUp(self):
        self.lookup = LookupModule()
        self.default_facts = {
            'openshift': {
                'common': {}
            }
        }

    def test_openshift_version(self):
        for regions_enabled in (True, False):
            for version, deployment_type, default_predicates in TEST_VARS:
                version = version + '.1'
                yield self.check_defaults_version, version, deployment_type, default_predicates, regions_enabled

    def check_defaults_version(self, version, deployment_type, default_predicates,
                               regions_enabled):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift_version'] = version
        facts['openshift']['common']['deployment_type'] = deployment_type
        results = self.lookup.run(None, variables=facts,
                                  regions_enabled=regions_enabled)
        if regions_enabled:
            assert_equal(results, default_predicates + [REGION_PREDICATE])
        else:
            assert_equal(results, default_predicates)

    def test_release_defaults(self):
        for regions_enabled in (True, False):
            for release, deployment_type, default_predicates in TEST_VARS:
                yield self.check_defaults_release, release, deployment_type, default_predicates, regions_enabled

    def test_v_release_defaults(self):
        for regions_enabled in (True, False):
            for release, deployment_type, default_predicates in TEST_VARS:
                yield self.check_defaults_release, 'v' + release, deployment_type, default_predicates, regions_enabled

    def test_trunc_openshift_release(self):
        for release, deployment_type, default_predicates in TEST_VARS:
            release = release + '.1'
            yield self.check_defaults_release, release, deployment_type, default_predicates, False

    def check_defaults_release(self, release, deployment_type, default_predicates,
                               regions_enabled):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift_release'] = release
        facts['openshift']['common']['deployment_type'] = deployment_type
        results = self.lookup.run(None, variables=facts,
                                  regions_enabled=regions_enabled)
        if regions_enabled:
            assert_equal(results, default_predicates + [REGION_PREDICATE])
        else:
            assert_equal(results, default_predicates)

    def test_short_version_defaults(self):
        for regions_enabled in (True, False):
            for short_version, deployment_type, default_predicates in TEST_VARS:
                yield self.check_defaults_short_version, short_version, deployment_type, default_predicates, regions_enabled

    def check_defaults_short_version(self, short_version, deployment_type, default_predicates,
                                     regions_enabled):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['short_version'] = short_version
        facts['openshift']['common']['deployment_type'] = deployment_type
        results = self.lookup.run(None, variables=facts,
                                  regions_enabled=regions_enabled)
        if regions_enabled:
            assert_equal(results, default_predicates + [REGION_PREDICATE])
        else:
            assert_equal(results, default_predicates)

    def test_short_version_kwarg(self):
        for regions_enabled in (True, False):
            for short_version, deployment_type, default_predicates in TEST_VARS:
                yield self.check_defaults_short_version_kwarg, short_version, deployment_type, default_predicates, regions_enabled

    def check_defaults_short_version_kwarg(self, short_version, deployment_type, default_predicates,
                                           regions_enabled):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['deployment_type'] = deployment_type
        results = self.lookup.run(None, variables=facts,
                                  regions_enabled=regions_enabled,
                                  short_version=short_version)
        if regions_enabled:
            assert_equal(results, default_predicates + [REGION_PREDICATE])
        else:
            assert_equal(results, default_predicates)

    def test_deployment_type_kwarg(self):
        for regions_enabled in (True, False):
            for short_version, deployment_type, default_predicates in TEST_VARS:
                yield self.check_defaults_deployment_type_kwarg, short_version, deployment_type, default_predicates, regions_enabled

    def check_defaults_deployment_type_kwarg(self, short_version, deployment_type,
                                             default_predicates, regions_enabled):
        facts = copy.deepcopy(self.default_facts)
        facts['openshift']['common']['short_version'] = short_version
        results = self.lookup.run(None, variables=facts,
                                  regions_enabled=regions_enabled,
                                  deployment_type=deployment_type)
        if regions_enabled:
            assert_equal(results, default_predicates + [REGION_PREDICATE])
        else:
            assert_equal(results, default_predicates)

    def test_only_kwargs(self):
        for regions_enabled in (True, False):
            for short_version, deployment_type, default_predicates in TEST_VARS:
                yield self.check_defaults_only_kwargs, short_version, deployment_type, default_predicates, regions_enabled

    def check_defaults_only_kwargs(self, short_version, deployment_type,
                                   default_predicates, regions_enabled):
        facts = copy.deepcopy(self.default_facts)
        results = self.lookup.run(None, variables=facts,
                                  regions_enabled=regions_enabled,
                                  short_version=short_version,
                                  deployment_type=deployment_type)
        if regions_enabled:
            assert_equal(results, default_predicates + [REGION_PREDICATE])
        else:
            assert_equal(results, default_predicates)
