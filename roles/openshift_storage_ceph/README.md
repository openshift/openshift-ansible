OpenShift Ceph Cluster
===========================

OpenShift Ceph Cluster Configuration

This role handles the configuration of Ceph cluster by deploying a single instance of a Ceph monitor and manager.
Once that's up and running, operators will have to interact with the Ceph CLI/interface to further pursue the deployment.

Requirements
------------

* Ansible 2.4

Dependencies
------------

* openshift_hosted_facts
* openshift_repos
* lib_openshift

Example Playbook
----------------

```yaml
- name: configure ceph hosts
  hosts: oo_first_master
  roles:
  - role: openshift_storage_ceph
```

License
-------

Apache License, Version 2.0

Author Information
------------------

Sébastien Han (seb@redhat.com)
