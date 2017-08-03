OpenShift/Atomic Enterprise Node Facts
================================

Node facts collector

Requirements
------------

* Ansible 2.2

Role Variables
--------------

| name                                           | description                              | default  | required | choices |
|------------------------------------------------|------------------------------------------|----------|----------|---------|
| r_openshift_node_facts_annotations             | Node annotations                         | None     |          |         |
| r_openshift_node_facts_debug_level             | Node debug lovel                         |          |          |         |
| r_openshift_node_facts_dns_ip                  |                                          |          |          |         |
| r_openshift_node_facts_env_vars                |                                          | None     |          |         |
| r_openshift_node_facts_iptables_sync_period    |                                          | None     |          |         |
| r_openshift_node_facts_kubelet_args            |                                          | None     |          |         |
| r_openshift_node_facts_labels                  | Node labels                              | None     |          |         |
| r_openshift_node_facts_local_quota_per_fsgroup |                                          | None     |          |         |
| r_openshift_node_facts_oreg_url                |                                          | None     |          |         |
| r_openshift_node_facts_osn_image               |                                          | None     |          |         |
| r_openshift_node_facts_osn_ovs_image           |                                          | None     |          |         |
| r_openshift_node_facts_osn_storage_plugin_deps | Store plugins to install on the node     | None     |          |         |
| r_openshift_node_facts_proxy_mode              |                                          | iptables |          |         |
| r_openshift_node_facts_schedulable             | If set pods can be scheduled on the node | None     |          |         |
| r_openshift_node_facts_sdn_mtu                 |                                          | None     |          |         |
| r_openshift_node_facts_set_node_ip             |                                          | None     |          |         |


Dependencies
------------

openshift_facts

Example Playbook
----------------

Notes
-----

TODO

License
-------

Apache License, Version 2.0

Author Information
------------------

TODO
