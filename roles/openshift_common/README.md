OpenShift Common
================

OpenShift common installation and configuration tasks.

Requirements
------------

A RHEL 7.1 host pre-configured with access to the rhel-7-server-rpms,
rhel-7-server-extra-rpms, and rhel-7-server-ose-beta-rpms repos.

Role Variables
--------------

| Name                          | Default value                |                                        |
|-------------------------------|------------------------------|----------------------------------------|
| openshift_debug_level         | 0                            | Global openshift debug log verbosity   |
| openshift_hostname_workaround | True                         | Workaround needed to set hostname to IP address |
| openshift_hostname            | openshift_public_ip if openshift_hostname_workaround else ansible_fqdn | hostname to use for this instance |
| openshift_public_ip           | UNDEF (Required)             | Public IP address to use for this host |
| openshift_env                 | default                      | Envrionment name if multiple OpenShift instances |

Dependencies
------------

os_firewall
openshift_repos

Example Playbook
----------------

TODO

License
-------

Apache License, Version 2.0

Author Information
------------------

TODO
