package preflight

import (
	"testing"

	. ".."
)

func TestPreflightFailAll(t *testing.T) {
	PlaybookTest{
		Path:     "playbooks/preflight_fail_all.yml",
		ExitCode: 2,
		Output: []string{
			"Failure summary",
			"Cannot install all of the necessary packages",
			"origin-clients",
			"origin-master",
			"origin-node",
			"origin-sdn-ovs",
			"python-httplib2",
			"failed=1",
		},
	}.Run(t)
}
