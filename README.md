[![Join the chat at https://gitter.im/openshift/openshift-ansible](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/openshift/openshift-ansible)
[![Build Status](https://travis-ci.org/openshift/openshift-ansible.svg?branch=master)](https://travis-ci.org/openshift/openshift-ansible)
[![Coverage Status](https://coveralls.io/repos/github/openshift/openshift-ansible/badge.svg?branch=master)](https://coveralls.io/github/openshift/openshift-ansible?branch=master)

NOTICE
======

Master branch is closed! A major refactor is ongoing in devel-40.
Changes for 3.x should be made directly to the latest release branch they're
relevant to and backported from there.

WARNING
=======

This branch is under heavy development.  If you are interested in deploying a
working cluster, please utilize a release branch.

# OpenShift Ansible

This repository contains [Ansible](https://www.ansible.com/) roles and
playbooks to install, upgrade, and manage
[OpenShift](https://www.openshift.com/) clusters.

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

- Ansible >= 2.7.8
- Jinja >= 2.7
- pyOpenSSL
- python-lxml

----

Fedora:

```
dnf install -y ansible pyOpenSSL python-cryptography python-lxml
```

## Simple all-in-one localhost Installation
This assumes that you've installed the base dependencies and you're running on
Fedora or RHEL
```
git clone https://github.com/openshift/openshift-ansible
cd openshift-ansible
sudo ansible-playbook -i inventory/hosts.localhost playbooks/prerequisites.yml
sudo ansible-playbook -i inventory/hosts.localhost playbooks/deploy_cluster.yml
```

# Quickstart

Install the new installer from https://www.github.com/openshift/installer

Construct a proper install-config.yml, and make a copy called
install-config-ansible.yml.

## Hosts
You will need the following hosts

### Boostrap host
This is a special host that is not part of the cluster but is required to be
available to help the cluster bootstrap itself.  This is not a bastion host,
it will initially be part of the cluster and should be able to communicate with
the masters in the cluster.

### Masters
You need 1 or 3 masters.

### Workers
You need 0 or more workers.  Note, by default, masters are unschedulable so
you will need one or more workers if you want to schedule workloads.

## DNS
4.x installs require specific dns records to be in place, and there is no way
to complete an install without working DNS.  You are in charge of ensuring the
following DNS records are resolvable from your cluster, the openshift-ansible
installer will not make any attempt to do any of this for you.

First, the output of ```hostname``` on each host must be resolvable to other hosts.
The nodes will communicate with each other based on this value.

install-config.yml value of 'baseDomain' must be a working domain.

### A records
```sh
<clustername>-api.<baseDomain> # ex: mycluster-api.example.com
<clustername>-master-0.<baseDomain> # ex: mycluster-master-0.example.com
<clustername>-etcd-0.<baseDomain> # ex: mycluster-etcd-0.example.com
<clustername>-bootstrap.<baseDomain> # ex: mycluster-bootstrap.example.com
```

Note: There should be a master/etcd record for each master host in your cluster
(either 1 or 3).  etcd hosts must be master hosts, and the records must resolve
to the same host for each master/etcd record, respectively.

### SRV records
```sh
SRV _etcd-client-ssl._tcp.<clustername>.<baseDomain> '1 1 2379 <clustername>-etcd-0.<baseDomain>'
SRV _etcd-server-ssl._tcp.<clustername>.<baseDomain> '1 1 2380 <clustername>-etcd-0.<baseDomain>'
...
SRV _etcd-client-ssl._tcp.<clustername>.<baseDomain> '1 1 2379 <clustername>-etcd-<N-1>.<baseDomain>'
SRV _etcd-server-ssl._tcp.<clustername>.<baseDomain> '1 1 2380 <clustername>-etcd-<N-1>.<baseDomain>'

# ex: _etcd-client-ssl._tcp.mycluster.example.com '1 1 2379 mycluster-etcd-0.example.com'
```

Consult with your DNS provider about the proper way to create SRV records.  In
any case, there should be a client and server SRV record for each etcd backend,
and you MUST use the etcd FQDN you created earlier, not the master or any other
record.

## Inventory
Check out inventory/40_basic_inventory.ini for an example.

## Generate ignition configs
Use the openshift-install command to generate ignition configs utilizing the
install-config.yml you created earlier.  This will consume the install-config.yml
file, so ensure you have copied the file as mentioned previously.

```sh
openshift-install create ignition-configs
```

## Run playbook
playbooks/deploy_cluster_40.yml

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
