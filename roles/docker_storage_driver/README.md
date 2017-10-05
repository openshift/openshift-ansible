Docker Storage Driver
=====================

Returns the current Docker storage driver according to `docker info`.

Requirements
------------

* Ansible 2.2
* Docker

Role Variables
--------------

`docker_storage_driver` (out)

* Name of the current storage driver (`devicemapper`, `overlay2`, etc)

Example Playbook
----------------

```
- hosts: nodes
  gather_facts: no
  roles:
  - role: docker_storage_driver
  tasks:
  - debug:
      msg: "Storage Driver: {{ docker_storage_driver }}"
```

License
-------

Apache License, Version 2.0

Author Information
------------------

Matthew Barnes <mbarnes@redhat.com>
