# Contributing

Thank you for contributing to OpenShift Ansible. This document explains how the
repository is organized, and how to submit contributions.

**Table of Contents**

<!-- TOC depthFrom:2 depthTo:4 withLinks:1 updateOnSave:1 orderedList:0 -->

- [Introduction](#introduction)
- [Submitting contributions](#submitting-contributions)
- [Running tests and other verification tasks](#running-tests-and-other-verification-tasks)
	- [Running only specific tasks](#running-only-specific-tasks)
- [Appendix](#appendix)
	- [Tricks](#tricks)
		- [Activating a virtualenv managed by tox](#activating-a-virtualenv-managed-by-tox)
		- [Limiting the unit tests that are run](#limiting-the-unit-tests-that-are-run)
		- [Finding unused Python code](#finding-unused-python-code)

<!-- /TOC -->

## Introduction

Before submitting code changes, get familiarized with these documents:

- [Core Concepts](docs/core_concepts_guide.adoc)
- [Best Practices Guide](docs/best_practices_guide.adoc)
- [Style Guide](docs/style_guide.adoc)
- [Repository Structure](docs/repo_structure.md)

Please consider opening an issue or discussing on an existing one if you are
planning to work on something larger, to make sure your time investment is
something that can be merged to the repository.

## Submitting contributions

1. [Fork](https://help.github.com/articles/fork-a-repo/) this repository and
   [create a work branch in your fork](https://help.github.com/articles/github-flow/).
2. Go through the documents mentioned in the [introduction](#introduction).
3. Make changes and commit. You may want to review your changes and
   [run tests](#running-tests-and-other-verification-tasks) before pushing your
   branch.
4. [Open a Pull Request](https://help.github.com/articles/creating-a-pull-request/).
   Give it a meaningful title explaining the changes you are proposing, and
   then add further details in the description.

One of the repository maintainers will then review the PR and trigger tests, and
possibly start a discussion that goes on until the PR is ready to be merged.
This process is further explained in the
[Pull Request process](docs/pull_requests.md) document.

If you get no timely feedback from a project contributor / maintainer, sorry for
the delay. You can help us speed up triaging, reviewing and eventually merging
contributions by requesting a review or tagging in a comment
[someone who has worked on the files](https://help.github.com/articles/tracing-changes-in-a-file/)
you're proposing changes to.

---

**Note**: during the review process, you may add new commits to address review
comments or change existing commits. However, before getting your PR merged,
please [squash commits](https://help.github.com/articles/about-git-rebase/) to a
minimum set of meaningful commits.

If you've broken your work up into a set of sequential changes and each commit
pass the tests on their own then that's fine. If you've got commits fixing typos
or other problems introduced by previous commits in the same PR, then those
should be squashed before merging.

If you are new to Git, these links might help:

- https://git-scm.com/book/en/v2/Git-Tools-Rewriting-History
- http://gitready.com/advanced/2009/02/10/squashing-commits-with-rebase.html

---

## Simple all-in-one localhost installation
```
git clone https://github.com/openshift/openshift-ansible
cd openshift-ansible
sudo ansible-playbook -i inventory/hosts.localhost playbooks/prerequisites.yml
sudo ansible-playbook -i inventory/hosts.localhost playbooks/deploy_cluster.yml
```

## Development process
Most changes can be applied by re-running the config playbook. However, while
the config playbook will run faster the second time through it's still going to
take a very long time. As such, you may wish to run a smaller subsection of the
installation playbooks. You can for instance run the node, master, or hosted
playbooks in playbooks/openshift-node/config.yml,
playbooks/openshift-master/config.yml, playbooks/openshift-hosted/config.yml
respectively.

We're actively working to refactor the playbooks into smaller discrete
components and we'll be documenting that structure shortly, for now those are
the most sensible logical units of work.

## Running tests and other verification tasks

We use [`tox`](http://readthedocs.org/docs/tox/) to manage virtualenvs where
tests and other verification tasks are run. We use
[`pytest`](https://docs.pytest.org/) as our test runner.

Alternatively to `tox`, one can use
[`detox`](https://pypi.python.org/pypi/detox/) for running verification tasks in
parallel. Note that while `detox` may be useful in development to make use of
multiple cores, it can be buggy at times and produce flakes, thus we do not use
it in our [CI](docs/continuous_integration.md) jobs.

```
pip install tox
```

To run all tests and verification tasks:

```
tox
```

---

**Note**: before running `tox` or `detox`, ensure that the only virtualenvs
within the repository root are the ones managed by `tox`, those in a `.tox`
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

### Running only specific tasks

The [tox configuration](tox.ini) describes environments based on either Python 2
or Python 3. Each environment is associated with a command that is executed in
the context of a virtualenv, with a specific version of Python, installed
dependencies, environment variables and so on. To list the environments
available:

```
tox -l
```

To run the command of a particular environment, e.g., `flake8` on Python 2.7:

```
tox -e py27-flake8
```

To run the command of a particular environment in a clean virtualenv, e.g.,
`pylint` on Python 3.5:

```
tox -re py35-pylint
```

The `-r` flag recreates existing environments, useful to force dependencies to
be reinstalled.

## Appendix

### Tricks

Here are some useful tips that might improve your workflow while working on this repository.

#### Git Hooks

Git hooks are included in this repository to aid in development. Check
out the README in the
[hack/hooks](http://github.com/openshift/openshift-ansible/blob/master/hack/hooks/README.md)
directory for more information.

#### Activating a virtualenv managed by tox

If you want to enter a virtualenv created by tox to do additional debugging, you
can activate it just like any other virtualenv (py27-flake8 environment in this
example):

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

#### Finding unused Python code

If you are contributing with Python code, you can use the tool
[`vulture`](https://pypi.python.org/pypi/vulture) to verify that you are not
introducing unused code by accident.

This tool is not used in an automated form in CI nor otherwise because it may
produce both false positives and false negatives. Still, it can be helpful to
detect dead code that escapes our eyes.
