OpenShift/Atomic Enterprise Common
===================================

OpenShift/Atomic Enterprise common installation and configuration tasks.

Requirements
------------

A RHEL 7.1 host pre-configured with access to the rhel-7-server-rpms,
rhel-7-server-extra-rpms, and rhel-7-server-ose-3.0-rpms repos.

Role Variables
--------------

| Name                      | Default value     |                                             |
|---------------------------|-------------------|---------------------------------------------|
| openshift_cluster_id      | default           | Cluster name if multiple OpenShift clusters |
| openshift_debug_level     | 2                 | Global openshift debug log verbosity        |
| openshift_hostname        | UNDEF             | Internal hostname to use for this host (this value will set the hostname on the system) |
| openshift_ip              | UNDEF             | Internal IP address to use for this host    |
| openshift_public_hostname | UNDEF             | Public hostname to use for this host        |
| openshift_public_ip       | UNDEF             | Public IP address to use for this host      |
| openshift_portal_net      | UNDEF             | Service IP CIDR |

Dependencies
------------

os_firewall
openshift_facts
openshift_repos

Example Playbook
----------------

TODO

License
-------

Apache License, Version 2.0

Author Information
------------------

Jason DeTiberus (jdetiber@redhat.com)
