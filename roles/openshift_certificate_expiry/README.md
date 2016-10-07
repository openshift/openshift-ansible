OpenShift Certificate Expiration Checker
========================================

OpenShift certificate expiration checking. Be warned of certificates
expiring within a configurable window of days, and notified of
certificates which have already expired. Certificates examined
include:

* Master/Node Service Certificates
* Router/Registry Service Certificates from etcd secrets
* Master/Node/Router/Registry/Admin `kubeconfig`s
* Etcd certificates



Requirements
------------

* None


Role Variables
--------------

From this role:

| Name                     | Default value | Description                                                                         |
|--------------------------|---------------|-------------------------------------------------------------------------------------|
| `config_base`            | `/etc/origin` | Base openshift config directory                                                     |
| `warning_days`           | `30`          | Flag certificates which will expire in this many days from now                      |
| `show_all`               | `False`       | Include healthy (non-expired and non-warning) certificates in results               |
| `generate_report`        | `False`       | Generate an HTML report of the expiry check results                                 |
| `save_json_results`      | `False`       | Save expiry check results as a json file                                            |
| `result_dir`             | `/tmp`        | Directory in which to put check results and generated reports                       |


Dependencies
------------

* None

Example Playbook
----------------

```
- name: Check cert expirys
  hosts: all
  become: yes
  gather_facts: no
  roles:
  - role: openshift_certificate_expiry
```


License
-------

Apache License, Version 2.0

Author Information
------------------

Tim Bielawa (tbielawa@redhat.com)
