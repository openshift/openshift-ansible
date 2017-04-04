Role Name
=========

Offline etcd migration of data from v2 to v3

Requirements
------------

It is expected all consumers of the etcd data are not accessing the data.
Otherwise the migrated data can be out-of-sync with the v2 and can result in unhealthy etcd cluster.

The role itself is responsible for:
- checking etcd cluster health and raft status before the migration
- checking of presence of any v3 data (in that case the migration is stopped)
- migration of v2 data to v3 data (including attaching leases of keys prefixed with "/kubernetes.io/events" and "/kubernetes.io/masterleases" string)
- validation of migrated data (all v2 keys and in v3 keys and are set to the identical value)

The migration itself requires an etcd member to be down in the process. Once the migration is done, the etcd member is started.

Role Variables
--------------

TBD

Dependencies
------------

- etcd_common
- lib_utils

Example Playbook
----------------

```yaml
- name: Migrate etcd data from v2 to v3
  hosts: oo_etcd_to_config
  gather_facts: no
  tasks:
  - include_role:
      name: openshift_etcd_migrate
    vars:
      etcd_peer: "{{ ansible_default_ipv4.address }}"
```

License
-------

Apache License, Version 2.0

Author Information
------------------

Jan Chaloupka (jchaloup@redhat.com)
