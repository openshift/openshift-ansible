# openshift_storage_nfs_lvm

This role is useful to create and export nfs disks for openshift persistent volumes.
It does so by creating lvm partitions on an already setup pv/vg, creating xfs 
filesystem on each partition, mounting the partitions, exporting the mounts via NFS
and creating a json file for each mount that an openshift master can use to
create persistent volumes.

## Requirements

* Ansible 2.2
* NFS server with NFS, iptables, and everything setup
* A lvm volume group created on the nfs server (default: openshiftvg)
* The lvm volume needs to have as much free space as you are allocating

## Role Variables

| Name                                              | Default value         | Description                                                                          |
|---------------------------------------------------|-----------------------|--------------------------------------------------------------------------------------|
| r_openshift_storage_nfs_lvm_nfs_export_options    | *(rw,sync,all_squash) | Options of NFS exports                                                               |
| r_openshift_storage_nfs_lvm_mount_dir             | /exports/openshift    | Directory, where the created partitions should be mounted.                           |
| r_openshift_storage_nfs_lvm_export_dir_mode       | 0700                  | Mode on the nfs-exported directory.                                                  |
| r_openshift_storage_nfs_lvm_volume_group          | openshiftvg           | Volume Group to use.                                                                 |
| r_openshift_storage_nfs_lvm_volume_prefix         | os-pv                 | Volume name prefix. Useful if you are using the nfs server for more than one cluster |
| r_openshift_storage_nfs_lvm_volume_size           | 1                     | Size of the volumes/partitions in Gigabytes.                                         |
| r_openshift_storage_nfs_lvm_volume_num_start      | 1                     | Where to start the volume number numbering.                                          |
| r_openshift_storage_nfs_lvm_volume_count          | 0                     | How many volumes/partitions to create. (will not create any volumes by default)      |
| r_openshift_storage_nfs_lvm_volume_reclaim_policy | Recycle               | Volume reclaim policy of the PersistentVolume.                                       |

## Dependencies

None

## Example Playbook

With this playbook, 2 5Gig lvm partitions are created, named stg5g0003 and stg5g0004
Both of them are mounted into `/exports/openshift` directory.  Both directories are 
exported via NFS.  json files are created in /root.

    - hosts: nfsservers
      become: no
      remote_user: root
      gather_facts: no
      roles:
        - role: openshift_storage_nfs_lvm
          r_openshift_storage_nfs_lvm_mount_dir: /exports/openshift
          r_openshift_storage_nfs_lvm_volume_prefix: "stg"
          r_openshift_storage_nfs_lvm_volume_size: 5
          r_openshift_storage_nfs_lvm_volume_num_start: 3
          r_openshift_storage_nfs_lvm_volume_count: 2
          r_openshift_storage_nfs_lvm_volume_reclaim_policy: "Recycle"


## Full example


* Create an `inventory` file:
    ```
    [nfsservers]
    10.0.0.1
    10.0.0.2
    ```

* Create an ansible playbook, say `setupnfs.yaml`:
    ```
    - hosts: nfsservers
      become: no
      remote_user: root
      gather_facts: no
      roles:
        - role: openshift_storage_nfs_lvm
          r_openshift_storage_nfs_lvm_mount_dir: /exports/stg
          r_openshift_storage_nfs_lvm_volume_prefix: "stg"
          r_openshift_storage_nfs_lvm_volume_size: 5
          r_openshift_storage_nfs_lvm_volume_num_start: 3
          r_openshift_storage_nfs_lvm_volume_count: 2
          r_openshift_storage_nfs_lvm_volume_reclaim_policy: "Recycle"

* Run the playbook:
    ```
    ansible-playbook -i inventory setupnfs.yml
    ```

## License

Apache 2.0
