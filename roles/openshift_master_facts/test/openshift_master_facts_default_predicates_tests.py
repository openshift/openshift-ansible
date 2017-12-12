import pytest


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

DEFAULT_PREDICATES_3_6 = DEFAULT_PREDICATES_1_5

DEFAULT_PREDICATES_3_7 = [
    {'name': 'NoVolumeZoneConflict'},
    {'name': 'MaxEBSVolumeCount'},
    {'name': 'MaxGCEPDVolumeCount'},
    {'name': 'MaxAzureDiskVolumeCount'},
    {'name': 'MatchInterPodAffinity'},
    {'name': 'NoDiskConflict'},
    {'name': 'GeneralPredicates'},
    {'name': 'PodToleratesNodeTaints'},
    {'name': 'CheckNodeMemoryPressure'},
    {'name': 'CheckNodeDiskPressure'},
    {'name': 'NoVolumeNodeConflict'},
]

DEFAULT_PREDICATES_3_9 = DEFAULT_PREDICATES_3_8 = DEFAULT_PREDICATES_3_7

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
    ('3.6', 'origin', DEFAULT_PREDICATES_3_6),
    ('3.6', 'openshift-enterprise', DEFAULT_PREDICATES_3_6),
    ('3.7', 'origin', DEFAULT_PREDICATES_3_7),
    ('3.7', 'openshift-enterprise', DEFAULT_PREDICATES_3_7),
    ('3.8', 'origin', DEFAULT_PREDICATES_3_8),
    ('3.8', 'openshift-enterprise', DEFAULT_PREDICATES_3_8),
    ('3.9', 'origin', DEFAULT_PREDICATES_3_9),
    ('3.9', 'openshift-enterprise', DEFAULT_PREDICATES_3_9),
]


def assert_ok(predicates_lookup, default_predicates, regions_enabled, **kwargs):
    results = predicates_lookup.run(None, regions_enabled=regions_enabled, **kwargs)
    if regions_enabled:
        assert results == default_predicates + [REGION_PREDICATE]
    else:
        assert results == default_predicates


def test_openshift_version(predicates_lookup, openshift_version_fixture, regions_enabled):
    facts, default_predicates = openshift_version_fixture
    assert_ok(predicates_lookup, default_predicates, variables=facts, regions_enabled=regions_enabled)


@pytest.fixture(params=TEST_VARS)
def openshift_version_fixture(request, facts):
    version, deployment_type, default_predicates = request.param
    version += '.1'
    facts['openshift_version'] = version
    facts['openshift']['common']['deployment_type'] = deployment_type
    return facts, default_predicates


def test_openshift_release(predicates_lookup, openshift_release_fixture, regions_enabled):
    facts, default_predicates = openshift_release_fixture
    assert_ok(predicates_lookup, default_predicates, variables=facts, regions_enabled=regions_enabled)


@pytest.fixture(params=TEST_VARS)
def openshift_release_fixture(request, facts, release_mod):
    release, deployment_type, default_predicates = request.param
    facts['openshift_release'] = release_mod(release)
    facts['openshift']['common']['deployment_type'] = deployment_type
    return facts, default_predicates


def test_short_version(predicates_lookup, short_version_fixture, regions_enabled):
    facts, default_predicates = short_version_fixture
    assert_ok(predicates_lookup, default_predicates, variables=facts, regions_enabled=regions_enabled)


@pytest.fixture(params=TEST_VARS)
def short_version_fixture(request, facts):
    short_version, deployment_type, default_predicates = request.param
    facts['openshift']['common']['short_version'] = short_version
    facts['openshift']['common']['deployment_type'] = deployment_type
    return facts, default_predicates


def test_short_version_kwarg(predicates_lookup, short_version_kwarg_fixture, regions_enabled):
    facts, short_version, default_predicates = short_version_kwarg_fixture
    assert_ok(
        predicates_lookup, default_predicates, variables=facts,
        regions_enabled=regions_enabled, short_version=short_version)


@pytest.fixture(params=TEST_VARS)
def short_version_kwarg_fixture(request, facts):
    short_version, deployment_type, default_predicates = request.param
    facts['openshift']['common']['deployment_type'] = deployment_type
    return facts, short_version, default_predicates


def test_deployment_type_kwarg(predicates_lookup, deployment_type_kwarg_fixture, regions_enabled):
    facts, deployment_type, default_predicates = deployment_type_kwarg_fixture
    assert_ok(
        predicates_lookup, default_predicates, variables=facts,
        regions_enabled=regions_enabled, deployment_type=deployment_type)


@pytest.fixture(params=TEST_VARS)
def deployment_type_kwarg_fixture(request, facts):
    short_version, deployment_type, default_predicates = request.param
    facts['openshift']['common']['short_version'] = short_version
    return facts, deployment_type, default_predicates


def test_short_version_deployment_type_kwargs(
        predicates_lookup, short_version_deployment_type_kwargs_fixture, regions_enabled):
    short_version, deployment_type, default_predicates = short_version_deployment_type_kwargs_fixture
    assert_ok(
        predicates_lookup, default_predicates, regions_enabled=regions_enabled,
        short_version=short_version, deployment_type=deployment_type)


@pytest.fixture(params=TEST_VARS)
def short_version_deployment_type_kwargs_fixture(request):
    return request.param
