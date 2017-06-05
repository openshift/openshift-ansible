package preflight

import (
	"testing"

	. ".."
)

func TestPackageUpdateDepMissing(t *testing.T) {
	PlaybookTest{
		Path:     "playbooks/package_update_dep_missing.yml",
		ExitCode: 2,
		Output: []string{
			"check \"package_update\":",
			"Could not perform a yum update.",
			"break-yum-update-1.0-2.noarch requires package-that-does-not-exist",
		},
	}.Run(t)
}

func TestPackageUpdateRepoBroken(t *testing.T) {
	PlaybookTest{
		Path:     "playbooks/package_update_repo_broken.yml",
		ExitCode: 2,
		Output: []string{
			"check \"package_update\":",
			"Error with yum repository configuration: Cannot find a valid baseurl for repo",
		},
	}.Run(t)
}

func TestPackageUpdateRepoDisabled(t *testing.T) {
	PlaybookTest{
		Path:     "playbooks/package_update_repo_disabled.yml",
		ExitCode: 0,
		Output: []string{
			"CHECK [package_update",
		},
	}.Run(t)
}

func TestPackageUpdateRepoUnreachable(t *testing.T) {
	PlaybookTest{
		Path:     "playbooks/package_update_repo_unreachable.yml",
		ExitCode: 2,
		Output: []string{
			"check \"package_update\":",
			"Error getting data from at least one yum repository",
		},
	}.Run(t)
}

func TestPackageVersionMatches(t *testing.T) {
	PlaybookTest{
		Path:     "playbooks/package_version_matches.yml",
		ExitCode: 0,
		Output: []string{
			"CHECK [package_version",
		},
	}.Run(t)
}

func TestPackageVersionMismatches(t *testing.T) {
	PlaybookTest{
		Path:     "playbooks/package_version_mismatches.yml",
		ExitCode: 2,
		Output: []string{
			"check \"package_version\":",
			"Not all of the required packages are available at their requested version",
		},
	}.Run(t)
}

func TestPackageVersionMultiple(t *testing.T) {
	PlaybookTest{
		Path:     "playbooks/package_version_multiple.yml",
		ExitCode: 2,
		Output: []string{
			"check \"package_version\":",
			"Multiple minor versions of these packages are available",
		},
	}.Run(t)
}

func TestPackageAvailabilityMissingRequired(t *testing.T) {
	PlaybookTest{
		Path:     "playbooks/package_availability_missing_required.yml",
		ExitCode: 2,
		Output: []string{
			"check \"package_availability\":",
			"Cannot install all of the necessary packages.",
			"atomic-openshift",
		},
	}.Run(t)
}

func TestPackageAvailabilitySucceeds(t *testing.T) {
	PlaybookTest{
		Path:     "playbooks/package_availability_succeeds.yml",
		ExitCode: 0,
		Output: []string{
			"CHECK [package_availability",
		},
	}.Run(t)
}
