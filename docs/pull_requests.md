# Pull Request process

Pull Requests in the `openshift-ansible` project follow a
[Continuous](https://en.wikipedia.org/wiki/Continuous_integration)
[Integration](https://martinfowler.com/articles/continuousIntegration.html)
process that is similar to the process observed in other repositories such as
[`origin`](https://github.com/openshift/origin).

Whenever a
[Pull Request is opened](../CONTRIBUTING.md#submitting-contributions), some
automated test jobs must be successfully run before the PR can be merged.

Some of these jobs are automatically triggered, e.g., Travis, PAPR, and
Coveralls. Other jobs need to be manually triggered by a member of the
[Team OpenShift Ansible Contributors](https://github.com/orgs/openshift/teams/team-openshift-ansible-contributors).

## Triggering tests

We have two different Jenkins infrastructures, and, while that holds true, there
are two commands that trigger a different set of test jobs. We are working on
simplifying the workflow towards a single infrastructure in the future.

- **Test jobs on the older infrastructure**

  Members of the [OpenShift organization](https://github.com/orgs/openshift/people)
  can trigger the set of test jobs in the older infrastructure by writing a
  comment with the exact text `aos-ci-test` and nothing else.

  The Jenkins host is not publicly accessible. Test results are posted to S3
  buckets when complete, and links are available both at the bottom of the Pull
  Request page and as comments posted by
  [@openshift-bot](https://github.com/openshift-bot).

- **Test jobs on the newer infrastructure**

  Members of the
  [Team OpenShift Ansible Contributors](https://github.com/orgs/openshift/teams/team-openshift-ansible-contributors)
  can trigger the set of test jobs in the newer infrastructure by writing a
  comment containing `[test]` anywhere in the comment body.

  The [Jenkins host](https://ci.openshift.redhat.com/jenkins/job/test_pull_request_openshift_ansible/)
  is publicly accessible. Like for the older infrastructure, the result of each
  job is also posted to the Pull Request as comments and summarized at the
  bottom of the Pull Request page.

### Fedora tests

There are a set of tests that run on Fedora infrastructure. They are started
automatically with every pull request.

They are implemented using the [`PAPR` framework](https://github.com/projectatomic/papr).

To re-run tests, write a comment containing only `bot, retest this please`.

## Triggering merge

After a PR is properly reviewed and a set of
[required jobs](https://github.com/openshift/aos-cd-jobs/blob/master/sjb/test_status_config.yml)
reported successfully, it can be tagged for merge by a member of the
[Team OpenShift Ansible Contributors](https://github.com/orgs/openshift/teams/team-openshift-ansible-contributors)
by writing a comment containing `[merge]` anywhere in the comment body.

Tagging a Pull Request for merge puts it in an automated merge queue. The
[@openshift-bot](https://github.com/openshift-bot) monitors the queue and merges
PRs that pass all of the required tests.

### Manual merges

The normal process described above should be followed: `aos-ci-test` and
`[test]` / `[merge]`.

In exceptional cases, such as when known problems with the merge queue prevent
PRs from being merged, a PR may be manually merged if _all_ of these conditions
are true:

- [ ] Travis job must have passed (as enforced by GitHub)
- [ ] Must have passed `aos-ci-test` (as enforced by GitHub)
- [ ] Must have a positive review (as enforced by GitHub)
- [ ] Must have failed the `[merge]` queue with a reported flake at least twice
- [ ] Must have [issues labeled kind/test-flake](https://github.com/openshift/origin/issues?q=is%3Aopen+is%3Aissue+label%3Akind%2Ftest-flake) in [Origin](https://github.com/openshift/origin) linked in comments for the failures
- [ ] Content must not have changed since all of the above conditions have been met (no rebases, no new commits)

This exception is temporary and should be completely removed in the future once
the merge queue has become more stable.

Only members of the
[Team OpenShift Ansible Committers](https://github.com/orgs/openshift/teams/team-openshift-ansible-committers)
can perform manual merges.

## Useful links

- Repository containing Jenkins job definitions: https://github.com/openshift/aos-cd-jobs
- List of required successful jobs before merge: https://github.com/openshift/aos-cd-jobs/blob/master/sjb/test_status_config.yml
- Source code of the bot responsible for testing and merging PRs: https://github.com/openshift/test-pull-requests/
- Trend of the time taken by merge jobs: https://ci.openshift.redhat.com/jenkins/job/merge_pull_request_openshift_ansible/buildTimeTrend
