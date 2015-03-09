OpenShift SDN Master
====================

OpenShift SDN Master service installation

Requirements
------------

A host with the openshift_master role applied

Role Variables
--------------

From this role:
| Name                             | Default value         |                                                  |
|----------------------------------|-----------------------|--------------------------------------------------|
| openshift_sdn_master_debug_level | openshift_debug_level | Verbosity of the debug logs for openshift-master |

From openshift_common:
| Name                  | Default value |                                      |
|-----------------------|---------------|--------------------------------------|
| openshift_debug_level | 0             | Global openshift debug log verbosity |

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
