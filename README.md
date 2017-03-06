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

The
[master branch](https://github.com/openshift/openshift-ansible/tree/master)
tracks our current work **in development** and should be compatible
with the
[Origin master branch](https://github.com/openshift/origin/tree/master)
(code in development).

In addition to the master branch, we maintain stable branches
corresponding to upstream Origin releases, e.g.: we guarantee an
openshift-ansible 3.2 release will fully support an origin
[1.2 release](https://github.com/openshift/openshift-ansible/tree/release-1.2).
The most recent branch will often receive minor feature backports and
fixes.  Older branches will receive only critical fixes.

**Getting the right openshift-ansible release**

Follow this release pattern and you can't go wrong:

| Origin        | OpenShift-Ansible |
| ------------- | ----------------- |
| 1.3           | 3.3               |
| 1.4           | 3.4               |
| 1.*X*         | 3.*X*             |

If you're running from the openshift-ansible **master branch** we can
only guarantee compatibility with the newest origin releases **in
development**. Use a branch corresponding to your origin version if
you are not running a stable release.


## Setup

1. Install base dependencies:

    ***

    Requirements:
    - Ansible >= 2.2.0
    - Jinja >= 2.7
    - pyOpenSSL
    - python-lxml

    ***

    Fedora:
    ```
    dnf install -y ansible pyOpenSSL python-cryptography python-lxml
    ```

2. Setup for a specific cloud:

  - [AWS](http://github.com/openshift/openshift-ansible/blob/master/README_AWS.md)
  - [GCE](http://github.com/openshift/openshift-ansible/blob/master/README_GCE.md)
  - [local VMs](http://github.com/openshift/openshift-ansible/blob/master/README_libvirt.md)
  - Bring your own host deployments:
      - [OpenShift Enterprise](https://docs.openshift.com/enterprise/latest/install_config/install/advanced_install.html)
      - [OpenShift Origin](https://docs.openshift.org/latest/install_config/install/advanced_install.html)

## Containerized OpenShift Ansible

See [README_CONTAINER_IMAGE.md](README_CONTAINER_IMAGE.md) for information on how to package openshift-ansible as a container image.

## Installer Hooks

See the [hooks documentation](HOOKS.md).


## Contributing

See the [contribution guide](CONTRIBUTING.md).
