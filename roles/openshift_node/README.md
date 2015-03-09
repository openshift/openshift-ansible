OpenShift Node
==============

OpenShift Node service installation

Requirements
------------

One or more OpenShift Master servers.

A RHEL 7.1 host pre-configured with access to the rhel-7-server-rpms,
rhel-7-server-extras-rpms, and rhel-server-7-ose-beta-rpms repos.

Role Variables
--------------
From this role:
| Name                                     | Default value         |                                        |
|------------------------------------------|-----------------------|----------------------------------------|
| openshift_node_manage_service_externally | False                 | Should the openshift-node role manage the openshift-node service? |
| openshift_node_debug_level               | openshift_debug_level | Verbosity of the debug logs for openshift-node |
| openshift_master_public_ips              | UNDEF (Required)      | List of the public IPs for the openhift-master hosts |
| openshift_master_ips                     | UNDEF (Required)      | List of IP addresses for the openshift-master hosts to be used for node -> master communication |
| openshift_registry_url                   | UNDEF (Optional)      | Default docker registry to use |
| openshift_node_resources                 | { capacity: { cpu: , memory: } } | Resource specification for this node, cpu is the number of CPUs to advertise and memory is the amount of memory in bytes to advertise. Default values chosen when not set are the number of logical CPUs for the host and 75% of total system memory |

From openshift_common:
| Name                          |  Default Value      |                     | 
|-------------------------------|---------------------|---------------------|
| openshift_debug_level         | 0                   | Global openshift debug log verbosity |
| openshift_hostname_workaround | True                |                     |
| openshift_public_ip           | UNDEF (Required)    | Public IP address to use for this host |
| openshift_hostname            | openshift_public_ip if openshift_hostname_workaround else ansible_fqdn | hostname to use for this instance |

Dependencies
------------

openshift_common

Example Playbook
----------------

TODO

License
-------

Apache License, Version 2.0

Author Information
------------------

TODO
