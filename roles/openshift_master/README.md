OpenShift Master
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
