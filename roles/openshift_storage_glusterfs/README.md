OpenShift GlusterFS Cluster
===========================

OpenShift GlusterFS Cluster Installation

Requirements
------------

* Ansible 2.2

Role Variables
--------------

From this role:

| Name                                             | Default value           |                                         |
|--------------------------------------------------|-------------------------|-----------------------------------------|
| openshift_storage_glusterfs_timeout              | 300                     | Seconds to wait for pods to become ready
| openshift_storage_glusterfs_namespace            | 'default'               | Namespace in which to create GlusterFS resources
| openshift_storage_glusterfs_is_native            | True                    | GlusterFS should be containerized
| openshift_storage_glusterfs_nodeselector         | 'storagenode=glusterfs' | Selector to determine which nodes will host GlusterFS pods in native mode
| openshift_storage_glusterfs_image                | 'gluster/gluster-centos'| Container image to use for GlusterFS pods, enterprise default is 'rhgs3/rhgs-server-rhel7'
| openshift_storage_glusterfs_version              | 'latest'                | Container image version to use for GlusterFS pods
| openshift_storage_glusterfs_wipe                 | False                   | Destroy any existing GlusterFS resources and wipe storage devices. **WARNING: THIS WILL DESTROY ANY DATA ON THOSE DEVICES.**
| openshift_storage_glusterfs_heketi_is_native     | True                    | heketi should be containerized
| openshift_storage_glusterfs_heketi_image         | 'heketi/heketi'         | Container image to use for heketi pods, enterprise default is 'rhgs3/rhgs-volmanager-rhel7'
| openshift_storage_glusterfs_heketi_version       | 'latest'                | Container image version to use for heketi pods
| openshift_storage_glusterfs_heketi_admin_key     | ''                      | String to use as secret key for performing heketi commands as admin
| openshift_storage_glusterfs_heketi_user_key      | ''                      | String to use as secret key for performing heketi commands as user that can only view or modify volumes
| openshift_storage_glusterfs_heketi_topology_load | True                    | Load the GlusterFS topology information into heketi
| openshift_storage_glusterfs_heketi_url           | Undefined               | URL for the heketi REST API, dynamically determined in native mode
| openshift_storage_glusterfs_heketi_wipe          | False                   | Destroy any existing heketi resources, defaults to the value of `openshift_storage_glusterfs_wipe`

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
```

License
-------

Apache License, Version 2.0

Author Information
------------------

Jose A. Rivera (jarrpa@redhat.com)
