import pytest
import aos_version

from collections import namedtuple
Package = namedtuple('Package', ['name', 'version'])

expected_pkgs = set(['spam', 'eggs'])


@pytest.mark.parametrize('pkgs, requested_release, expect_not_found', [
    (
        [],
        '3.2.1',
        expected_pkgs,  # none found
    ),
    (
        [Package('spam', '3.2.1')],
        '3.2',
        ['eggs'],  # completely missing
    ),
    (
        [Package('spam', '3.2.1'), Package('eggs', '3.3.2')],
        '3.2',
        ['eggs'],  # not the right version
    ),
    (
        [Package('spam', '3.2.1'), Package('eggs', '3.2.1')],
        '3.2',
        [],  # all found
    ),
    (
        [Package('spam', '3.2.1'), Package('eggs', '3.2.1.5')],
        '3.2.1',
        [],  # found with more specific version
    ),
    (
        [Package('eggs', '1.2.3'), Package('eggs', '3.2.1.5')],
        '3.2.1',
        ['spam'],  # eggs found with multiple versions
    ),
])
def test_check_pkgs_for_precise_version(pkgs, requested_release, expect_not_found):
    if expect_not_found:
        with pytest.raises(aos_version.PreciseVersionNotFound) as e:
            aos_version._check_precise_version_found(pkgs, expected_pkgs, requested_release)
        assert set(expect_not_found) == set(e.value.problem_pkgs)
    else:
        aos_version._check_precise_version_found(pkgs, expected_pkgs, requested_release)


@pytest.mark.parametrize('pkgs, requested_release, expect_higher', [
    (
        [],
        '3.2.1',
        [],
    ),
    (
        [Package('spam', '3.2.1')],
        '3.2',
        [],  # more precise but not strictly higher
    ),
    (
        [Package('spam', '3.3')],
        '3.2.1',
        ['spam-3.3'],  # lower precision, but higher
    ),
    (
        [Package('spam', '3.2.1'), Package('eggs', '3.3.2')],
        '3.2',
        ['eggs-3.3.2'],  # one too high
    ),
    (
        [Package('eggs', '1.2.3'), Package('eggs', '3.2.1.5'), Package('eggs', '3.4')],
        '3.2.1',
        ['eggs-3.4'],  # multiple versions, one is higher
    ),
    (
        [Package('eggs', '3.2.1'), Package('eggs', '3.4'), Package('eggs', '3.3')],
        '3.2.1',
        ['eggs-3.4'],  # multiple versions, two are higher
    ),
])
def test_check_pkgs_for_greater_version(pkgs, requested_release, expect_higher):
    if expect_higher:
        with pytest.raises(aos_version.FoundHigherVersion) as e:
            aos_version._check_higher_version_found(pkgs, expected_pkgs, requested_release)
        assert set(expect_higher) == set(e.value.problem_pkgs)
    else:
        aos_version._check_higher_version_found(pkgs, expected_pkgs, requested_release)


@pytest.mark.parametrize('pkgs, expect_to_flag_pkgs', [
    (
        [],
        [],
    ),
    (
        [Package('spam', '3.2.1')],
        [],
    ),
    (
        [Package('spam', '3.2.1'), Package('eggs', '3.2.2')],
        [],
    ),
    (
        [Package('spam', '3.2.1'), Package('spam', '3.3.2')],
        ['spam'],
    ),
    (
        [Package('eggs', '1.2.3'), Package('eggs', '3.2.1.5'), Package('eggs', '3.4')],
        ['eggs'],
    ),
])
def test_check_pkgs_for_multi_release(pkgs, expect_to_flag_pkgs):
    if expect_to_flag_pkgs:
        with pytest.raises(aos_version.FoundMultiRelease) as e:
            aos_version._check_multi_minor_release(pkgs, expected_pkgs)
        assert set(expect_to_flag_pkgs) == set(e.value.problem_pkgs)
    else:
        aos_version._check_multi_minor_release(pkgs, expected_pkgs)
