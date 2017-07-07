OpenShift GlusterFS Cluster
===========================

OpenShift GlusterFS Cluster Configuration

This role handles the configuration of GlusterFS clusters. It can handle
two primary configuration scenarios:

* Configuring a new, natively-hosted GlusterFS cluster. In this scenario,
  GlusterFS pods are deployed on nodes in the OpenShift cluster which are
  configured to provide storage.
* Configuring a new, external GlusterFS cluster. In this scenario, the
  cluster nodes have the GlusterFS software pre-installed but have not
  been configured yet. The installer will take care of configuring the
  cluster(s) for use by OpenShift applications.
* Using existing GlusterFS clusters. In this scenario, one or more
  GlusterFS clusters are assumed to be already setup. These clusters can
  be either natively-hosted or external, but must be managed by a
  [heketi service](https://github.com/heketi/heketi).

As part of the configuration, a particular GlusterFS cluster may be
specified to provide backend storage for a natively-hosted Docker
registry.

Unless configured otherwise, a StorageClass will be automatically
created for each non-registry GlusterFS cluster. This will allow
applications which can mount PersistentVolumes to request
dynamically-provisioned GlusterFS volumes.

Requirements
------------

* Ansible 2.2

Host Groups
-----------

The following group is expected to be populated for this role to run:

* `[glusterfs]`

Additionally, the following group may be specified either in addition to or
instead of the above group to deploy a GlusterFS cluster for use by a natively
hosted Docker registry:

* `[glusterfs_registry]`

Host Variables
--------------

For configuring new clusters, the following role variables are available.

Each host in either of the above groups must have the following variable
defined:

| Name              | Default value | Description                             |
|-------------------|---------------|-----------------------------------------|
| glusterfs_devices | None          | A list of block devices that will be completely managed as part of a GlusterFS cluster. There must be at least one device listed. Each device must be bare, e.g. no partitions or LVM PVs. **Example:** '[ "/dev/sdb" ]'

In addition, each host may specify the following variables to further control
their configuration as GlusterFS nodes:

| Name               | Default value             | Description                             |
|--------------------|---------------------------|-----------------------------------------|
| glusterfs_cluster  | 1                         | The ID of the cluster this node should belong to. This is useful when a single heketi service is expected to manage multiple distinct clusters. **NOTE:** For natively-hosted clusters, all pods will be in the same OpenShift namespace
| glusterfs_hostname | openshift.node.nodename   | A hostname (or IP address) that will be used for internal GlusterFS communication
| glusterfs_ip       | openshift.common.ip       | An IP address that will be used by pods to communicate with the GlusterFS node
| glusterfs_zone     | 1                         | A zone number for the node. Zones are used within the cluster for determining how to distribute the bricks of GlusterFS volumes. heketi will try to spread each volumes' bricks as evenly as possible across all zones

Role Variables
--------------

This role has the following variables that control the integration of a
GlusterFS cluster into a new or existing OpenShift cluster:

| Name                                             | Default value           | Description                             |
|--------------------------------------------------|-------------------------|-----------------------------------------|
| openshift_storage_glusterfs_timeout              | 300                     | Seconds to wait for pods to become ready
| openshift_storage_glusterfs_namespace            | 'default'               | Namespace in which to create GlusterFS resources
| openshift_storage_glusterfs_is_native            | True                    | GlusterFS should be containerized
| openshift_storage_glusterfs_name                 | 'storage'               | A name to identify the GlusterFS cluster, which will be used in resource names
| openshift_storage_glusterfs_nodeselector         | 'glusterfs=storage-host'| Selector to determine which nodes will host GlusterFS pods in native mode. **NOTE:** The label value is taken from the cluster name
| openshift_storage_glusterfs_storageclass         | True                    | Automatically create a StorageClass for each GlusterFS cluster
| openshift_storage_glusterfs_image                | 'gluster/gluster-centos'| Container image to use for GlusterFS pods, enterprise default is 'rhgs3/rhgs-server-rhel7'
| openshift_storage_glusterfs_version              | 'latest'                | Container image version to use for GlusterFS pods
| openshift_storage_glusterfs_wipe                 | False                   | Destroy any existing GlusterFS resources and wipe storage devices. **WARNING: THIS WILL DESTROY ANY DATA ON THOSE DEVICES.**
| openshift_storage_glusterfs_heketi_is_native     | True                    | heketi should be containerized
| openshift_storage_glusterfs_heketi_image         | 'heketi/heketi'         | Container image to use for heketi pods, enterprise default is 'rhgs3/rhgs-volmanager-rhel7'
| openshift_storage_glusterfs_heketi_version       | 'latest'                | Container image version to use for heketi pods
| openshift_storage_glusterfs_heketi_admin_key     | auto-generated          | String to use as secret key for performing heketi commands as admin
| openshift_storage_glusterfs_heketi_user_key      | auto-generated          | String to use as secret key for performing heketi commands as user that can only view or modify volumes
| openshift_storage_glusterfs_heketi_topology_load | True                    | Load the GlusterFS topology information into heketi
| openshift_storage_glusterfs_heketi_url           | Undefined               | When heketi is native, this sets the hostname portion of the final heketi route URL. When heketi is external, this is the full URL to the heketi service.
| openshift_storage_glusterfs_heketi_port          | 8080                    | TCP port for external heketi service **NOTE:** This has no effect in native mode
| openshift_storage_glusterfs_heketi_wipe          | False                   | Destroy any existing heketi resources, defaults to the value of `openshift_storage_glusterfs_wipe`

Each role variable also has a corresponding variable to optionally configure a
separate GlusterFS cluster for use as storage for an integrated Docker
registry. These variables start with the prefix
`openshift_storage_glusterfs_registry_` and, for the most part, default to the
values in their corresponding non-registry variables. The following variables
are an exception:

| Name                                                  | Default value         | Description                             |
|-------------------------------------------------------|-----------------------|-----------------------------------------|
| openshift_storage_glusterfs_registry_namespace        | registry namespace    | Default is to use the hosted registry's namespace, otherwise 'default'
| openshift_storage_glusterfs_registry_name             | 'registry'            | This allows for the logical separation of the registry GlusterFS cluster from other GlusterFS clusters
| openshift_storage_glusterfs_registry_storageclass     | False                 | It is recommended to not create a StorageClass for GlusterFS clusters serving registry storage, so as to avoid performance penalties
| openshift_storage_glusterfs_registry_heketi_admin_key | auto-generated        | Separate from the above
| openshift_storage_glusterfs_registry_heketi_user_key  | auto-generated        | Separate from the above

Additionally, this role's behavior responds to the following registry-specific
variables:

| Name                                          | Default value                | Description                             |
|-----------------------------------------------|------------------------------|-----------------------------------------|
| openshift_hosted_registry_glusterfs_endpoints | glusterfs-registry-endpoints | The name for the Endpoints resource that will point the registry to the GlusterFS nodes
| openshift_hosted_registry_glusterfs_path      | glusterfs-registry-volume    | The name for the GlusterFS volume that will provide registry storage
| openshift_hosted_registry_glusterfs_readonly  | False                        | Whether the GlusterFS volume should be read-only
| openshift_hosted_registry_glusterfs_swap      | False                        | Whether to swap an existing registry's storage volume for a GlusterFS volume
| openshift_hosted_registry_glusterfs_swapcopy  | True                         | If swapping, copy the contents of the pre-existing registry storage to the new GlusterFS volume

Dependencies
------------

* os_firewall
* openshift_hosted_facts
* openshift_repos
* lib_openshift

Example Playbook
----------------

```
- name: Configure GlusterFS hosts
  hosts: oo_first_master
  roles:
  - role: openshift_storage_glusterfs
    when: groups.oo_glusterfs_to_config | default([]) | count > 0
```

License
-------

Apache License, Version 2.0

Author Information
------------------

Jose A. Rivera (jarrpa@redhat.com)
