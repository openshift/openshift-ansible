etcd_common
========================

Common resources for dependent etcd roles. E.g. default variables for:
* config directories
* certificates
* ports
* other settings

Or `delegated_serial_command` ansible module for executing a command on a remote node. E.g.

```yaml
- delegated_serial_command:
    command: /usr/bin/make_database.sh arg1 arg2
    creates: /path/to/database
```

Or etcdctl.yml playbook for installation of `etcdctl` aliases on a node (see example).

Dependencies
------------

openshift-repos

Example Playbook
----------------

**Drop etcdctl aliases**

```yaml
- include_role:
    name: etcd_common
    tasks_from: etcdctl
```

**Get access to common variables**

```yaml
# meta.yml of etcd
...
dependencies:
- { role: etcd_common }
```

License
-------

Apache License Version 2.0

Author Information
------------------

Jason DeTiberus (jdetiber@redhat.com)
