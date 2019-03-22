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

For OpenShift 4.x, this repo only provides playbooks necessary for scaling up an
existing 4.x cluster with RHEL hosts.

The [master branch](https://github.com/openshift/openshift-ansible/tree/master)
tracks our current work **in development**.

Requirements:

- Ansible >= 2.7.8
- pyOpenSSL
- python2-openshift

# Quickstart

## Install an OpenShift 4.x cluster
Install a cluster using the [OpenShift Installer](https://www.github.com/openshift/installer).

## Inventory
Create an inventory file with the `new_workers` group to identify the hosts which
should be added to the cluster.
```yaml

---
[new_workers]
mycluster-worker-0.example.com
mycluster-worker-1.example.com
mycluster-worker-2.example.com
```

## Run the scaleup playbook

```bash
ansible-playbook playbooks/openshift_node/scaleup.yml
```

# Further reading

## Complete Production Installation Documentation:

- [OpenShift Container Platform](https://docs.openshift.com/container-platform/3.11/install/running_install.html)
- [OpenShift Origin](https://docs.okd.io/latest/install/index.html)

## Containerized OpenShift Ansible

See [README_CONTAINER_IMAGE.md](README_CONTAINER_IMAGE.md) for information on how to package openshift-ansible as a container image.

## Installer Hooks

See the [hooks documentation](HOOKS.md).

## Contributing

See the [contribution guide](CONTRIBUTING.md).

## Building openshift-ansible RPMs and container images

See the [build instructions](BUILD.md).
