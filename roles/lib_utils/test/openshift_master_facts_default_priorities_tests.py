import pytest


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

DEFAULT_PRIORITIES_1_5 = [
    {'name': 'SelectorSpreadPriority', 'weight': 1},
    {'name': 'InterPodAffinityPriority', 'weight': 1},
    {'name': 'LeastRequestedPriority', 'weight': 1},
    {'name': 'BalancedResourceAllocation', 'weight': 1},
    {'name': 'NodePreferAvoidPodsPriority', 'weight': 10000},
    {'name': 'NodeAffinityPriority', 'weight': 1},
    {'name': 'TaintTolerationPriority', 'weight': 1}
]

DEFAULT_PRIORITIES_3_6 = DEFAULT_PRIORITIES_1_5

DEFAULT_PRIORITIES_3_9 = DEFAULT_PRIORITIES_3_8 = DEFAULT_PRIORITIES_3_7 = DEFAULT_PRIORITIES_3_6

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
    ('3.4', 'openshift-enterprise', DEFAULT_PRIORITIES_1_4),
    ('1.5', 'origin', DEFAULT_PRIORITIES_1_5),
    ('3.5', 'openshift-enterprise', DEFAULT_PRIORITIES_1_5),
    ('3.6', 'origin', DEFAULT_PRIORITIES_3_6),
    ('3.6', 'openshift-enterprise', DEFAULT_PRIORITIES_3_6),
    ('3.7', 'origin', DEFAULT_PRIORITIES_3_7),
    ('3.7', 'openshift-enterprise', DEFAULT_PRIORITIES_3_7),
    ('3.8', 'origin', DEFAULT_PRIORITIES_3_8),
    ('3.8', 'openshift-enterprise', DEFAULT_PRIORITIES_3_8),
    ('3.9', 'origin', DEFAULT_PRIORITIES_3_9),
    ('3.9', 'openshift-enterprise', DEFAULT_PRIORITIES_3_9),
]


def assert_ok(priorities_lookup, default_priorities, zones_enabled, **kwargs):
    results = priorities_lookup.run(None, zones_enabled=zones_enabled, **kwargs)
    if zones_enabled:
        assert results == default_priorities + [ZONE_PRIORITY]
    else:
        assert results == default_priorities


def test_openshift_version(priorities_lookup, openshift_version_fixture, zones_enabled):
    facts, default_priorities = openshift_version_fixture
    assert_ok(priorities_lookup, default_priorities, variables=facts, zones_enabled=zones_enabled)


@pytest.fixture(params=TEST_VARS)
def openshift_version_fixture(request, facts):
    version, deployment_type, default_priorities = request.param
    version += '.1'
    facts['openshift_version'] = version
    facts['openshift']['common']['deployment_type'] = deployment_type
    return facts, default_priorities


def test_openshift_release(priorities_lookup, openshift_release_fixture, zones_enabled):
    facts, default_priorities = openshift_release_fixture
    assert_ok(priorities_lookup, default_priorities, variables=facts, zones_enabled=zones_enabled)


@pytest.fixture(params=TEST_VARS)
def openshift_release_fixture(request, facts, release_mod):
    release, deployment_type, default_priorities = request.param
    facts['openshift_release'] = release_mod(release)
    facts['openshift']['common']['deployment_type'] = deployment_type
    return facts, default_priorities


def test_short_version(priorities_lookup, short_version_fixture, zones_enabled):
    facts, default_priorities = short_version_fixture
    assert_ok(priorities_lookup, default_priorities, variables=facts, zones_enabled=zones_enabled)


@pytest.fixture(params=TEST_VARS)
def short_version_fixture(request, facts):
    short_version, deployment_type, default_priorities = request.param
    facts['openshift']['common']['short_version'] = short_version
    facts['openshift']['common']['deployment_type'] = deployment_type
    return facts, default_priorities


def test_short_version_kwarg(priorities_lookup, short_version_kwarg_fixture, zones_enabled):
    facts, short_version, default_priorities = short_version_kwarg_fixture
    assert_ok(
        priorities_lookup, default_priorities, variables=facts,
        zones_enabled=zones_enabled, short_version=short_version)


@pytest.fixture(params=TEST_VARS)
def short_version_kwarg_fixture(request, facts):
    short_version, deployment_type, default_priorities = request.param
    facts['openshift']['common']['deployment_type'] = deployment_type
    return facts, short_version, default_priorities


def test_deployment_type_kwarg(priorities_lookup, deployment_type_kwarg_fixture, zones_enabled):
    facts, deployment_type, default_priorities = deployment_type_kwarg_fixture
    assert_ok(
        priorities_lookup, default_priorities, variables=facts,
        zones_enabled=zones_enabled, deployment_type=deployment_type)


@pytest.fixture(params=TEST_VARS)
def deployment_type_kwarg_fixture(request, facts):
    short_version, deployment_type, default_priorities = request.param
    facts['openshift']['common']['short_version'] = short_version
    return facts, deployment_type, default_priorities


def test_short_version_deployment_type_kwargs(
        priorities_lookup, short_version_deployment_type_kwargs_fixture, zones_enabled):
    short_version, deployment_type, default_priorities = short_version_deployment_type_kwargs_fixture
    assert_ok(
        priorities_lookup, default_priorities, zones_enabled=zones_enabled,
        short_version=short_version, deployment_type=deployment_type)


@pytest.fixture(params=TEST_VARS)
def short_version_deployment_type_kwargs_fixture(request):
    return request.param
