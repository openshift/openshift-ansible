[![Join the chat at https://gitter.im/openshift/openshift-ansible](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/openshift/openshift-ansible)
[![Build Status](https://travis-ci.org/openshift/openshift-ansible.svg?branch=master)](https://travis-ci.org/openshift/openshift-ansible)
[![Coverage Status](https://coveralls.io/repos/github/openshift/openshift-ansible/badge.svg?branch=master)](https://coveralls.io/github/openshift/openshift-ansible?branch=master)

# OpenShift Ansible

This repository contains [Ansible](https://www.ansible.com/) roles and
playbooks to install, upgrade, and manage
[OpenShift](https://www.openshift.com/) clusters.

**Note**: the Ansible playbooks in this repository require an RPM
package that provides `docker`. Currently, the RPMs from
[dockerproject.org](https://dockerproject.org/) do not provide this
requirement, though they may in the future. This limitation is being
tracked by
[#2720](https://github.com/openshift/openshift-ansible/issues/2720).

## Getting the correct version
When choosing an openshift release, ensure that the necessary origin packages
are available in your distribution's repository.  By default, openshift-ansible
will not configure extra repositories for testing or staging packages for
end users.

We recommend using a release branch. We maintain stable branches
corresponding to upstream Origin releases, e.g.: we guarantee an
openshift-ansible 3.2 release will fully support an origin
[1.2 release](https://github.com/openshift/openshift-ansible/tree/release-1.2).

The most recent branch will often receive minor feature backports and
fixes. Older branches will receive only critical fixes.

In addition to the release branches, the master branch
[master branch](https://github.com/openshift/openshift-ansible/tree/master)
tracks our current work **in development** and should be compatible
with the
[Origin master branch](https://github.com/openshift/origin/tree/master)
(code in development).



**Getting the right openshift-ansible release**

Follow this release pattern and you can't go wrong:

| Origin/OCP    | OpenShift-Ansible version | openshift-ansible branch |
| ------------- | ----------------- |----------------------------------|
| 1.3 / 3.3          | 3.3               | release-1.3 |
| 1.4 / 3.4          | 3.4               | release-1.4 |
| 1.5 / 3.5          | 3.5               | release-1.5 |
| 3.*X*         | 3.*X*             | release-3.x |

If you're running from the openshift-ansible **master branch** we can
only guarantee compatibility with the newest origin releases **in
development**. Use a branch corresponding to your origin version if
you are not running a stable release.


## Setup

Install base dependencies:

Requirements:

- Ansible >= 2.4.1.0
- Jinja >= 2.7
- pyOpenSSL
- python-lxml

----

Fedora:

```
dnf install -y ansible pyOpenSSL python-cryptography python-lxml
```

## OpenShift Installation Documentation:

- [OpenShift Enterprise](https://docs.openshift.com/enterprise/latest/install_config/install/advanced_install.html)
- [OpenShift Origin](https://docs.openshift.org/latest/install_config/install/advanced_install.html)

## Containerized OpenShift Ansible

See [README_CONTAINER_IMAGE.md](README_CONTAINER_IMAGE.md) for information on how to package openshift-ansible as a container image.

## Installer Hooks

See the [hooks documentation](HOOKS.md).

## Contributing

See the [contribution guide](CONTRIBUTING.md).

## Building openshift-ansible RPMs and container images

See the [build instructions](BUILD.md).
