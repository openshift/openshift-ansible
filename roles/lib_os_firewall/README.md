lib_os_firewall
===========

lib_os_firewall manages iptables firewall settings for a minimal use
case (Adding/Removing rules based on protocol and port number).

Note: firewalld is not supported on Atomic Host
https://bugzilla.redhat.com/show_bug.cgi?id=1403331

Requirements
------------

Ansible 2.2

Role Variables
--------------

| Name                      | Default |                                        |
|---------------------------|---------|----------------------------------------|
| os_firewall_allow         | []      | List of service,port mappings to allow |
| os_firewall_deny          | []      | List of service, port mappings to deny |

Dependencies
------------

None.

Example Playbook
----------------

Use iptables and open tcp ports 80 and 443:
```
---
- hosts: servers
  vars:
    os_firewall_use_firewalld: false
    os_firewall_allow:
    - service: httpd
      port: 80/tcp
    - service: https
      port: 443/tcp
  tasks:
  - include_role:
      name: lib_os_firewall

  - name: set allow rules
    os_firewall_manage_iptables:
      name: "{{ item.service }}"
      action: add
      protocol: "{{ item.port.split('/')[1] }}"
      port: "{{ item.port.split('/')[0] }}"
    with_items: "{{ os_firewall_allow }}"
```


License
-------

Apache License, Version 2.0

Author Information
------------------
Jason DeTiberus - jdetiber@redhat.com
