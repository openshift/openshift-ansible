OpenShift Node DNS resolver
===========================

Configure dnsmasq to act as a DNS resolver for an OpenShift node.

Requirements
------------

Role Variables
--------------

From this role:

| Name                                                | Default value | Description                                                                       |
|-----------------------------------------------------|---------------|-----------------------------------------------------------------------------------|
| openshift_node_dnsmasq_install_network_manager_hook | true          | Install NetworkManager hook updating /etc/resolv.conf with local dnsmasq instance |

Dependencies
------------

* openshift_common
* openshift_node_facts

License
-------

Apache License Version 2.0
