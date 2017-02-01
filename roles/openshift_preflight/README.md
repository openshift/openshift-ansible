OpenShift Preflight Checks
==========================

This role detects common problems prior to installing OpenShift.

Requirements
------------

* Ansible 2.2+

Role Variables
--------------

None

Dependencies
------------

None

Example Playbook
----------------

```yaml
---
- hosts: OSEv3
  roles:
    - openshift_preflight/init

- hosts: OSEv3
  name: checks that apply to all hosts
  gather_facts: no
  ignore_errors: yes
  roles:
    - openshift_preflight/common

- hosts: OSEv3
  name: verify check results
  gather_facts: no
  roles:
    - openshift_preflight/verify_status
```

License
-------

Apache License Version 2.0

Author Information
------------------

Customer Success team (dev@lists.openshift.redhat.com)
