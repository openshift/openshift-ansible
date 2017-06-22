OpenShift/Atomic Enterprise Master
==================================

Master service installation

Requirements
------------

* Ansible 2.2
* A RHEL 7.1 host pre-configured with access to the rhel-7-server-rpms,
rhel-7-server-extras-rpms, and rhel-7-server-ose-3.0-rpms repos.

Role Variables
--------------

From this role:

| Name                                             | Default value         |                                                                               |
|---------------------------------------------------|-----------------------|-------------------------------------------------------------------------------|
| openshift_master_debug_level                      | openshift_debug_level | Verbosity of the debug logs for master                                        |
| openshift_node_ips                                | []                    | List of the openshift node ip addresses to pre-register when master starts up |
| oreg_url                                          | UNDEF                 | Default docker registry to use                                                |
| oreg_url_master                                   | UNDEF                 | Default docker registry to use, specifically on the master                    |
| openshift_master_api_port                         | UNDEF                 |                                                                               |
| openshift_master_console_port                     | UNDEF                 |                                                                               |
| openshift_master_api_url                          | UNDEF                 |                                                                               |
| openshift_master_console_url                      | UNDEF                 |                                                                               |
| openshift_master_public_api_url                   | UNDEF                 |                                                                               |
| openshift_master_public_console_url               | UNDEF                 |                                                                               |
| openshift_master_saconfig_limit_secret_references | false                 |                                                                               |

From openshift_common:

| Name                          | Default Value  |                                        |
|-------------------------------|----------------|----------------------------------------|
| openshift_debug_level         | 2              | Global openshift debug log verbosity   |
| openshift_public_ip           | UNDEF          | Public IP address to use for this host |
| openshift_hostname            | UNDEF          | hostname to use for this instance      |

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
