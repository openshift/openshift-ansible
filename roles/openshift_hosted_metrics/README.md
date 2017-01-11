OpenShift Metrics with Hawkular
====================

OpenShift Metrics Installation

Requirements
------------

* Ansible 2.2
* It requires subdomain fqdn to be set.
* If persistence is enabled, then it also requires NFS.

Role Variables
--------------

From this role:

| Name                                            | Default value         |                                                             |
|-------------------------------------------------|-----------------------|-------------------------------------------------------------|
| openshift_hosted_metrics_deploy                 | `False`               | If metrics should be deployed                               |
| openshift_hosted_metrics_public_url             | null                  | Hawkular metrics public url                                 |
| openshift_hosted_metrics_storage_nfs_directory  | `/exports`            | Root export directory.                                      |
| openshift_hosted_metrics_storage_volume_name    | `metrics`             | Metrics volume within openshift_hosted_metrics_volume_dir   |
| openshift_hosted_metrics_storage_volume_size    | `10Gi`                | Metrics volume size                                         |
| openshift_hosted_metrics_storage_nfs_options    | `*(rw,root_squash)`   | NFS options for configured exports.                         |
| openshift_hosted_metrics_duration               | `7`                   | Metrics query duration                                      |
| openshift_hosted_metrics_resolution             | `10s`                 | Metrics resolution                                          |


Dependencies
------------
openshift_facts
openshift_examples
openshift_master_facts

Example Playbook
----------------

```
- name: Configure openshift-metrics
  hosts: oo_first_master
  roles:
  - role: openshift_hosted_metrics
```

License
-------

Apache License, Version 2.0

Author Information
------------------

Jose David Martín (j.david.nieto@gmail.com)
