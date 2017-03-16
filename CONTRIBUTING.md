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
parallel.

Note: while `detox` may be useful in development to make use of multiple cores,
it can be buggy at times and produce flakes, thus we do not use it in our CI.


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

The reason for this recommendation is that extraneous virtualenvs cause tools
such as `pylint` to take a very long time going through files that are part of
the virtualenv, and test discovery to go through lots of irrelevant files and
potentially fail.

---

List the test environments available:

```
tox -l
```

Run all of the tests and linters with:

```
tox
```

Run all of the tests linters in parallel (may flake):

```
detox
```

### Run only unit tests or some specific linter

Run a particular test environment (`flake8` on Python 2.7 in this case):

```
tox -e py27-flake8
```

Run a particular test environment in a clean virtualenv (`pylint` on Python 3.5
in this case):

```
tox -re py35-pylint
```

### Tricks

#### Activating a virtualenv managed by tox

If you want to enter a virtualenv created by tox to do additional
testing/debugging (py27-flake8 env in this case):

```
source .tox/py27-flake8/bin/activate
```

#### Limiting the unit tests that are run

During development, it might be useful to constantly run just a single test file
or test method, or to pass custom arguments to `pytest`:

```
tox -e py27-unit -- path/to/test/file.py
```

Anything after `--` is passed directly to `pytest`. To learn more about what
other flags you can use, try:

```
tox -e py27-unit -- -h
```

As a practical example, the snippet below shows how to list all tests in a
certain file, and then execute only one test of interest:

```
$ tox -e py27-unit -- roles/lib_openshift/src/test/unit/test_oc_project.py --collect-only --no-cov
...
collected 1 items
<Module 'roles/lib_openshift/src/test/unit/test_oc_project.py'>
  <UnitTestCase 'OCProjectTest'>
    <TestCaseFunction 'test_adding_a_project'>
...
$ tox -e py27-unit -- roles/lib_openshift/src/test/unit/test_oc_project.py -k test_adding_a_project
```

Among other things, this can be used for instance to see the coverage levels of
individual modules as we work on improving tests.

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
