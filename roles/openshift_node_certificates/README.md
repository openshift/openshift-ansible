OpenShift Node Certificates
===========================

This role determines if OpenShift node certificates must be created, delegates certificate creation to the `openshift_ca_host` and then deploys those certificates to node hosts which this role is being applied to.

Requirements
------------

* Ansible 2.2

Role Variables
--------------

From `openshift_ca`:

| Name                                | Default value                                                           | Description                                                                                                               |
|-------------------------------------|-------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|

From this role:

| Name                                | Default value                                                           | Description                                                                                                               |
|-------------------------------------|-------------------------------------------------------------------------|---------------------------------------------------------------------------------------------------------------------------|
| openshift_generated_configs_dir     | `{{ openshift.common.config_base }}/generated-configs`                  | Directory in which per-node generated config directories will be created on the `openshift_ca_host`.                      |
| openshift_node_cert_subdir          | `node-{{ openshift.common.hostname }}`                                  | Directory within `openshift_generated_configs_dir` where per-node certificates will be placed on the `openshift_ca_host`. |
| openshift_node_cert_expire_days     | `730` (2 years)                                                         | Validity of the certificates in days. Works only with OpenShift version 1.5 (3.5) and later.                              |
| openshift_node_config_dir           | `{{ openshift.common.config_base }}/node`                               | Node configuration directory in which certificates will be deployed on nodes.                                             |
| openshift_node_generated_config_dir | `{{ openshift_generated_configs_dir }}/{{ openshift_node_cert_subdir }` | Full path to the per-node generated config directory.                                                                     |

Dependencies
------------

* openshift_ca

Example Playbook
----------------

```
- name: Create OpenShift Node Certificates
  hosts: nodes
  roles:
  - role: openshift_node_certificates
```

License
-------

Apache License Version 2.0

Author Information
------------------

Jason DeTiberus (jdetiber@redhat.com)
