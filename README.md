[![Join the chat at https://gitter.im/openshift/openshift-ansible](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/openshift/openshift-ansible)
[![Build Status](https://travis-ci.org/openshift/openshift-ansible.svg?branch=master)](https://travis-ci.org/openshift/openshift-ansible)

# OpenShift Ansible

This repository contains [Ansible](https://www.ansible.com/) code to install,
upgrade and manage [OpenShift](https://www.openshift.com/) clusters.

**Note**: the Ansible playbooks in this repository require an RPM package that
provides `docker`. Currently, the RPMs from
[dockerproject.org](https://dockerproject.org/) do not provide this requirement,
though they may in the future. This limitation is being tracked by
[#2720](https://github.com/openshift/openshift-ansible/issues/2720).

## Branches and tags

The [master branch](https://github.com/openshift/openshift-ansible/tree/master)
tracks our current work and should be compatible with both [Origin master
branch](https://github.com/openshift/origin/tree/master) and the [most recent
Origin stable release](https://github.com/openshift/origin/releases). Currently
that's v1.4 and v1.3.x. In addition to the master branch, we maintain stable
branches corresponding to upstream Origin releases, e.g.:
[release-1.2](https://github.com/openshift/openshift-ansible/tree/release-1.2).
The most recent branch will often receive minor feature backports and fixes.
Older branches will receive only critical fixes.

Releases are tagged periodically from active branches and are versioned 3.x
corresponding to Origin releases 1.x. We unfortunately started with 3.0 and it's
not practical to start over at 1.0.

## Setup

1. Install base dependencies:

    ***

    Requirements:
    - Ansible >= 2.2.0
    - Jinja >= 2.7

    ***

    Fedora:
    ```
    dnf install -y ansible pyOpenSSL python-cryptography
    ```

2. Setup for a specific cloud:

  - [AWS](http://github.com/openshift/openshift-ansible/blob/master/README_AWS.md)
  - [GCE](http://github.com/openshift/openshift-ansible/blob/master/README_GCE.md)
  - [local VMs](http://github.com/openshift/openshift-ansible/blob/master/README_libvirt.md)
  - Bring your own host deployments:
      - [OpenShift Enterprise](https://docs.openshift.com/enterprise/latest/install_config/install/advanced_install.html)
      - [OpenShift Origin](https://docs.openshift.org/latest/install_config/install/advanced_install.html)

## Contributing

See the [contribution guide](CONTRIBUTING.md).
