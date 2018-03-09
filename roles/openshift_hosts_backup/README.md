OpenShift Hosts Backup
======================

This role creates a backup of OpenShift configuration files and helper services
such as iptables, dnsmasq, etc.

Requirements
------------

* Ansible 2.2+

Role Variables
--------------

None

Dependencies
------------

Example Playbook
----------------

```yaml
---
- hosts: masters,nodes
  name: run OpenShift hosts backup
  roles:
    - openshift_hosts_backup
```

License
-------

Apache License Version 2.0

Author Information
------------------

Customer Success team (dev@lists.openshift.redhat.com)
