dns
===

Configure a DNS server serving IPs of all the nodes of the cluster

Requirements
------------

None

Role Variables
--------------

| Name | Mandatory / Optional | Description |
|------|----------------------|-------------|
| `dns_zones` | Mandatory | DNS zones in which we must find the hosts |
| `dns_forwarders` | If not set, the DNS will be a recursive non-forwarding DNS server | DNS forwarders to delegate the requests for hosts outside of `dns_zones` |
| `dns_all_hosts` | Mandatory | Exhaustive list of hosts |

Dependencies
------------

None

Example Playbook
----------------

    - hosts: dns_hosts
      roles:
      - role: dns
        dns_forwarders: [ '8.8.8.8', '8.8.4.4' ]
        dns_zones: [ novalocal, openstacklocal ]
        dns_all_hosts: "{{ g_all_hosts }}"

License
-------

ASL 2.0

Author Information
------------------

OpenShift operations, Red Hat, Inc
