OpenShift Persistent Local Volumes
==================================

OpenShift Persistent Local Volumes

Requirements
------------

Role Variables
--------------

| Name                           | Default value |                                                                           |
|--------------------------------|---------------|---------------------------------------------------------------------------|
| persistentlocalstorage_project | local-storage | The namespace where the Persistent Local Volume Provider will be deployed |
| persistentlocalstorage_classes | []            | Storage classes that will be created                                      |

Dependencies
------------


Example Playbook
----------------

```
- name: Create persistent Local Storage Provider
  hosts: oo_first_master
  vars:
    persistentlocalstorage_project: local-storage
    persistentlocalstorage_classes:
    - ssd
    - hdd
  roles:
  - role: openshift_persistentlocalstorage
```

License
-------

Apache License, Version 2.0

Author Information
------------------

Diego Abelenda (diego.abelenda@camptocamp.com)
