package example

import (
	"testing"

	. ".."
)

// TestPing and TestFail below are just examples of tests that involve running
// 'ansible-playbook' with a given playbook and verifying the outcome. Real
// tests look similar, but call more interesting playbooks.

func TestPing(t *testing.T) {
	PlaybookTest{
		Path:   "playbooks/test_ping.yml",
		Output: []string{"[test ping]"},
	}.Run(t)
}

func TestFail(t *testing.T) {
	PlaybookTest{
		Path:     "playbooks/test_fail.yml",
		ExitCode: 2,
		Output:   []string{"[test fail]", `"msg": "Failed as requested from task"`},
	}.Run(t)
}
