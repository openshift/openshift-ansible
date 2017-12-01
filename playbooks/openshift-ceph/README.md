# OpenShift Ceph Playbooks

These playbooks are intended to deploy Rook, a Kubernetes orchestrator to deploy storage systems.
In the present case, Rook has been configured to deploy a minimal Ceph cluster with a single monitor and manager.

## Prequisites

This playbook requires Openshift Storage Ceph to be installed, to install it set this variable:

```yaml
openshift_storage_ceph_install: true
```

## Playbook: uninstall.yml

This playbook is intended to uninstall all Ceph related resources
on an existing OpenShift cluster.
It has all the same requirements and behaviors as `config.yml`.

If the variable `openshift_storage_ceph_wipe` is set as True,
it clears the backend data as well.

## Role: openshift_storage_ceph

The bulk of the work is done by the `openshift_storage_ceph` role. This
role can handle the deployment of Ceph (if it is to be hosted on the
OpenShift cluster), the registration of Ceph nodes (hosted or standalone),
and (if specified) integration as backend storage for a hosted Docker registry.

See the documentation in the role's directory for further details.

## Role: openshift_hosted

The `openshift_hosted` role recognizes `ceph` as a possible storage
backend for a hosted docker registry. It will also, if configured, handle the
swap of an existing registry's backend storage to a Ceph volume.
