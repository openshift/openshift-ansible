Ansible AWX
===========

Creates an AWX instance. You can point playbooks/openshift-autoheal to it.

# Installation

See the [installation playbook](../../playbooks/awx) uses the
following variables:

- `awx_install`: `true` - install/update. `false` - uninstall.
  Defaults to `false`.

Requirements
------------

This role requires a running OpenShift cluster.
