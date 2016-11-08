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

### Others

```
.
└── git                 Contains some helper scripts for repository maintenance.
```

## Building RPMs

See the [RPM build instructions](BUILD.md).

## Running tests

We use [Nose](http://readthedocs.org/docs/nose/) as a test runner. Make sure it
is installed along with other test dependencies:

```
pip install -r utils/test-requirements.txt
```

Run the tests with:

```
nosetests
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
