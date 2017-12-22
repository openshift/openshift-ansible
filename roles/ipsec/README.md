# OpenShift IPSec Playbook

## Overview
This playbook enables IPSec in your existing OpenShift/OCP cluster according to the [Red Hat documentation](https://docs.openshift.com/container-platform/3.6/admin_guide/ipsec.html). It uses existing secrets to perform these actions and uses your current inventory to perform the configuration.

## Requirements
- Ansible >= 2.2
- OpenShift >= 3.4

## Usage
Using the playbook is simple. It will work out of the box with your current inventory. Use the playbook and point to your current inventory file.
```bash
[]$ ansible-playbook -i /path/to/openshift-inventory /path/to/openshift-ansible/playbooks/byo/ipsec.yml
```

## Checking
To check the status of iptables:
```bash
[]$ ipsec status | grep connections:
000 Total IPsec connections: loaded 7, active 1
```
Or, for all nodes:
```bash
[]$ ansible -i /path/to/openshift-inventory nodes -m shell -a "ipsec status | grep connections"
192.168.122.67 | SUCCESS | rc=0 >>
000 Total IPsec connections: loaded 1, active 1
000 State Information: DDoS cookies not required, Accepting new IKE connections

192.168.122.175 | SUCCESS | rc=0 >>
000 Total IPsec connections: loaded 1, active 1
000 State Information: DDoS cookies not required, Accepting new IKE connections
```

And to see connection traffic:
```bash
[]$ ipsec whack --trafficstatus
006 #2: "private#192.168.122.175/32"[1] ...192.168.122.175, type=ESP, add_time=1509134156, inBytes=636519, outBytes=73886, id='CN=192.168.122.175'
```
Or, for all nodes:
```bash
[]$ ansible -i /path/to/openshift-inventory nodes -a "ipsec whack --trafficstatus"
192.168.122.67 | SUCCESS | rc=0 >>
006 #2: "private#192.168.122.175/32"[1] ...192.168.122.175, type=ESP, add_time=1510242657, inBytes=68474, outBytes=9886, id='CN=192.168.122.175'

192.168.122.175 | SUCCESS | rc=0 >>
006 #2: "private#192.168.122.67/32"[1] ...192.168.122.67, type=ESP, add_time=1510242657, inBytes=9886, outBytes=68474, id='CN=192.168.122.67'
```
