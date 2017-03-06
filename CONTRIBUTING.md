# Contributing

Thank you for contributing to OpenShift Ansible. This document explains how the
repository is organized, and how to submit contributions.

## Introduction

Before submitting code changes, get familiarized with these documents:

- [Core Concepts](https://github.com/openshift/openshift-ansible/blob/master/docs/core_concepts_guide.adoc)
- [Best Practices Guide](https://github.com/openshift/openshift-ansible/blob/master/docs/best_practices_guide.adoc)
- [Style Guide](https://github.com/openshift/openshift-ansible/blob/master/docs/style_guide.adoc)

## Repository structure

### Ansible

```
.
├── inventory           Contains dynamic inventory scripts, and examples of
│                       Ansible inventories.
├── library             Contains Python modules used by the playbooks.
├── playbooks           Contains Ansible playbooks targeting multiple use cases.
└── roles               Contains Ansible roles, units of shared behavior among
                        playbooks.
```

#### Ansible plugins

These are plugins used in playbooks and roles:

```
.
├── ansible-profile
├── callback_plugins
├── filter_plugins
└── lookup_plugins
```

### Scripts

```
.
├── bin                 [DEPRECATED] Contains the `bin/cluster` script, a
│                       wrapper around the Ansible playbooks that ensures proper
│                       configuration, and facilitates installing, updating,
│                       destroying and configuring OpenShift clusters.
│                       Note: this tool is kept in the repository for legacy
│                       reasons and will be removed at some point.
└── utils               Contains the `atomic-openshift-installer` command, an
                        interactive CLI utility to install OpenShift across a
                        set of hosts.
```

### Documentation

```
.
└── docs                Contains documentation for this repository.
```

### Tests

```
.
└── test                Contains tests.
```

## Building RPMs

See the [RPM build instructions](BUILD.md).

## Running tests

We use [tox](http://readthedocs.org/docs/tox/) to manage virtualenvs and run
tests. Alternatively, tests can be run using
[detox](https://pypi.python.org/pypi/detox/) which allows for running tests in
parallel


```
pip install tox detox
```

---

Note: before running `tox` or `detox`, ensure that the only virtualenvs within
the repository root are the ones managed by `tox`, those in a `.tox`
subdirectory.

Use this command to list paths that are likely part of a virtualenv not managed
by `tox`:

```
$ find . -path '*/bin/python' | grep -vF .tox
```

Extraneous virtualenvs cause tools such as `pylint` to take a very long time
going through files that are part of the virtualenv.

---

List the test environments available:
```
tox -l
```

Run all of the tests with:
```
tox
```

Run all of the tests in parallel with detox:
```
detox
```

Running a particular test environment (python 2.7 flake8 tests in this case):
```
tox -e py27-flake8
```

Running a particular test environment in a clean virtualenv (python 3.5 pylint
tests in this case):
```
tox -r -e py35-pylint
```

If you want to enter the virtualenv created by tox to do additional
testing/debugging (py27-flake8 env in this case):
```
source .tox/py27-flake8/bin/activate
```

## Submitting contributions

1. Go through the guides from the [introduction](#Introduction).
2. Fork this repository, and create a work branch in your fork.
3. Make changes and commit. You may want to review your changes and run tests
   before pushing your branch.
4. Open a Pull Request.

One of the repository maintainers will then review the PR and submit it for
testing.

The `default` test job is publicly accessible at
https://ci.openshift.redhat.com/jenkins/job/openshift-ansible/. The other jobs
are run on a different Jenkins host that is not publicly accessible, however the
test results are posted to S3 buckets when complete.

The test output of each job is also posted to the Pull Request as comments.

---

## Appendix

### Finding unused Python code

If you are contributing with Python code, you can use the tool
[`vulture`](https://pypi.python.org/pypi/vulture) to verify that you are not
introducing unused code by accident.

This tool is not used in an automated form in CI nor otherwise because it may
produce both false positives and false negatives. Still, it can be helpful to
detect dead code that escapes our eyes.
