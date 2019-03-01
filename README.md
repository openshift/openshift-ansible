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

- Ansible >= 2.6, Ansible 2.7 is supported
- Jinja >= 2.7
- pyOpenSSL
- python-lxml

----

Fedora:

```
dnf install -y ansible pyOpenSSL python-cryptography python-lxml
```

Additional requirements:

Logging:

- java-1.8.0-openjdk-headless
- patch

Metrics:

- httpd-tools

## Simple all-in-one localhost Installation
This assumes that you've installed the base dependencies and you're running on
Fedora or RHEL
```
git clone https://github.com/openshift/openshift-ansible
cd openshift-ansible
sudo ansible-playbook -i inventory/hosts.localhost playbooks/prerequisites.yml
sudo ansible-playbook -i inventory/hosts.localhost playbooks/deploy_cluster.yml
```
## Node Group Definition and Mapping
In 3.10 and newer all members of the [nodes] inventory group must be assigned an
`openshift_node_group_name`. This value is used to select the configmap that
configures each node. By default there are three configmaps created; one for
each node group defined in `openshift_node_groups` and they're named
`node-config-master` `node-config-infra` `node-config-compute`. It's important
to note that the configmap is also the authoritative definition of node labels,
the old `openshift_node_labels` value is effectively ignored.

There are also two configmaps that label nodes into multiple roles, these are
not recommended for production clusters, however they're named
`node-config-all-in-one` and `node-config-master-infra` if you'd like to use
them to deploy non production clusters.

The default set of node groups is defined in
[roles/openshift_facts/defaults/main.yml] like so

```
openshift_node_groups:
  - name: node-config-master
    labels:
      - 'node-role.kubernetes.io/master=true'
    edits: []
  - name: node-config-infra
    labels:
      - 'node-role.kubernetes.io/infra=true'
    edits: []
  - name: node-config-compute
    labels:
      - 'node-role.kubernetes.io/compute=true'
    edits: []
  - name: node-config-master-infra
    labels:
      - 'node-role.kubernetes.io/infra=true,node-role.kubernetes.io/master=true'
    edits: []
  - name: node-config-all-in-one
    labels:
      - 'node-role.kubernetes.io/infra=true,node-role.kubernetes.io/master=true,node-role.kubernetes.io/compute=true'
    edits: []
```

When configuring this in the INI based inventory this must be translated into a
Python dictionary. Here's an example of a group named `node-config-all-in-one`
which is suitable for an All-In-One installation with
kubeletArguments.pods-per-core set to 20

```
openshift_node_groups=[{'name': 'node-config-all-in-one', 'labels': ['node-role.kubernetes.io/master=true', 'node-role.kubernetes.io/infra=true', 'node-role.kubernetes.io/compute=true'], 'edits': [{ 'key': 'kubeletArguments.pods-per-core','value': ['20']}]}]
```

For upgrades, the upgrade process will block until you have the required
configmaps in the openshift-node namespace. Please define
`openshift_node_groups` as explained above or accept the defaults and run the
playbooks/openshift-master/openshift_node_group.yml playbook to have them
created for you automatically.


## Complete Production Installation Documentation:

- [OpenShift Container Platform](https://docs.openshift.com/container-platform/latest/install_config/install/advanced_install.html)
- [OpenShift Origin](https://docs.okd.io/latest/install/index.html)

## Containerized OpenShift Ansible

See [README_CONTAINER_IMAGE.md](README_CONTAINER_IMAGE.md) for information on how to package openshift-ansible as a container image.

## Installer Hooks

See the [hooks documentation](HOOKS.md).

## Contributing

See the [contribution guide](CONTRIBUTING.md).

## Building openshift-ansible RPMs and container images

See the [build instructions](BUILD.md).
