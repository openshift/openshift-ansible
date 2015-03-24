OpenShift SDN Node
==================

OpenShift SDN Node service installation

Requirements
------------

A host with the openshift_node role applied

Role Variables
--------------

From this role:
| Name                           | Default value         |                                                  |
|--------------------------------|-----------------------|--------------------------------------------------|
| openshift_sdn_node_debug_level | openshift_debug_level | Verbosity of the debug logs for openshift-master |


From openshift_node:
| Name                  | Default value    |                                      |
|-----------------------|------------------|--------------------------------------|
| openshift_master_ips  | UNDEF (Required) | List of IP addresses for the openshift-master hosts to be used for node -> master communication |


From openshift_common:
| Name                          | Default value       |                                        |
|-------------------------------|---------------------|----------------------------------------|
| openshift_debug_level         | 0                   | Global openshift debug log verbosity   |
| openshift_public_ip           | UNDEF (Required)    | Public IP address to use for this host |
| openshift_hostname            | UNDEF (Required)    | hostname to use for this instance |

Dependencies
------------


Example Playbook
----------------

TODO

License
-------

Apache License, Version 2.0

Author Information
------------------

TODO
