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
| openshift_node_debug_level               | openshift_debug_level | Verbosity of the debug logs for openshift-node |
| openshift_registry_url                   | UNDEF (Optional)      | Default docker registry to use |

From openshift_common:
| Name                          |  Default Value      |                     | 
|-------------------------------|---------------------|---------------------|
| openshift_debug_level         | 0                   | Global openshift debug log verbosity |
| openshift_public_ip           | UNDEF (Required)    | Public IP address to use for this host |
| openshift_hostname            | UNDEF (Required)    | hostname to use for this instance |

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
