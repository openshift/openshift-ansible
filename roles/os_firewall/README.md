OS Firewall
===========

OS Firewall manages firewalld and iptables firewall settings for a minimal use
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
| os_firewall_use_firewalld | False   | If false, use iptables                 |
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
  roles:
  - os_firewall
```

Use firewalld and open tcp port 443 and close previously open tcp port 80:
```
---
- hosts: servers
  vars:
    os_firewall_allow:
    - service: https
      port: 443/tcp
    os_firewall_deny:
    - service: httpd
      port: 80/tcp
  roles:
  - os_firewall
```

License
-------

Apache License, Version 2.0

Author Information
------------------
Jason DeTiberus - jdetiber@redhat.com
