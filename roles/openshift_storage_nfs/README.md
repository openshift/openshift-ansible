OpenShift NFS Server
====================

OpenShift NFS Server Installation

Requirements
------------

This role is intended to be applied to the [nfs] host group which is
separate from OpenShift infrastructure components.

Requires access to the 'nfs-utils' package.

Role Variables
--------------

From this role:
| Name                          | Default value         |                                                  |
|-------------------------------|-----------------------|--------------------------------------------------|
| openshift_nfs_exports_dir     | /var/export           | Root export directory.                           |
| openshift_nfs_registry_volume | regvol                | Registry volume within openshift_nfs_exports_dir |
| openshift_nfs_export_options  | *(rw,sync,all_squash) | NFS options for configured exports.              |


From openshift_common:
| Name                          | Default Value  |                                        |
|-------------------------------|----------------|----------------------------------------|
| openshift_debug_level         | 2              | Global openshift debug log verbosity   |


Dependencies
------------



Example Playbook
----------------

- name: Configure nfs hosts
  hosts: oo_nfs_to_config
  roles:
  - role: openshift_storage_nfs

License
-------

Apache License, Version 2.0

Author Information
------------------

Andrew Butcher (abutcher@redhat.com)
