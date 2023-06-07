[![Join the chat at https://gitter.im/openshift/openshift-ansible](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/openshift/openshift-ansible)
[![Build Status](https://travis-ci.org/openshift/openshift-ansible.svg?branch=master)](https://travis-ci.org/openshift/openshift-ansible)

# OpenShift Ansible
This repository contains [Ansible](https://www.ansible.com/) roles and
playbooks for [OpenShift](https://www.openshift.com/) clusters.

## Previous OpenShift Ansible 3.x releases
For 3.x releases of OpenShift Ansible please reference the release branch for
specific versions.  The last 3.x release is 
[3.11 release](https://github.com/openshift/openshift-ansible/tree/release-3.11).

## OpenShift 4.x
Installation of OpenShift 4.x uses a command-line installation wizard instead of
Ansible playbooks.  Learn more about the OpenShift Installer in this
[overview](https://github.com/openshift/installer/blob/master/docs/user/overview.md#installer-overview).

For OpenShift 4.x, this repository only provides playbooks necessary for scaling up or
upgrading RHEL hosts in an existing 4.x cluster.

The [master branch](https://github.com/openshift/openshift-ansible/tree/master)
tracks our current work **in development**.

Requirements: (localhost)

- Ansible >= 2.9.5
- OpenShift Client (oc)

# Quickstart

## Install an OpenShift 4.x cluster
Install a cluster using the [OpenShift Installer](https://www.github.com/openshift/installer).

## Create an Ansible Inventory
Create an inventory file with the appropriate groups and variables defined.
An example inventory can be found in [inventory/hosts.example](inventory/hosts.example).

Required variables include:

- `openshift_kubeconfig_path` - Path to the kubeconfig for the cluster

## Run the RHEL node scaleup playbook

```bash
cd openshift-ansible
ansible-playbook -i inventory/hosts playbooks/scaleup.yml
```

## Run the RHEL node upgrade playbook
Custom tasks can be performed during upgrades at different stages of the upgrade.
See the [hooks documentation](HOOKS.md) for more information.

```bash
cd openshift-ansible
ansible-playbook -i inventory/hosts playbooks/upgrade.yml
```

# Further reading

## Complete Production Installation Documentation:
- [OpenShift Container Platform](https://docs.openshift.com/container-platform/4.13/installing/index.html)
- [OKD](https://docs.okd.io/latest/installing/index.html) (formerly OpenShift Origin)

## Containerized OpenShift Ansible

See [README_CONTAINER_IMAGE.md](README_CONTAINER_IMAGE.md) for information on how to package openshift-ansible as a container image.

## Contributing

See the [contribution guide](CONTRIBUTING.md).

## Building openshift-ansible RPMs and container images

See the [build instructions](BUILD.md).
