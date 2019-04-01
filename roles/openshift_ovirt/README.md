# OpenShift oVirt

OpenShift Provisioned on Red Hat Virtualization and oVirt

The puprpose of the role is to create the VMs, by a recepie, using vars, and generate an inventory. \
The generated inventory can be merged into and openshift inventory(see examples dir[1]) and to ease the deployment a lot.

- [OpenShift oVirt](#openshift-ovirt)
  * [Role Tasks](#role-tasks)
  * [Role Variables](#role-variables)
  * [Examples](#examples)
    + [Manifest](#manifest)
    + [Playbook](#playbook)
  * [License](#license)

**Important note**: To make this role work you need to set this option on your _ansible.cfg_ file `jinja2_extensions = jinja2.ext.do`

## Role Tasks

- `main.yaml`: The entrypoint to the role. It invokes the following tasks below.
- `build_vm_list.yml`: Creates a list of virtual machine definitions and
  affinity groups based on a simple manifest (below)
- `create_vms.yaml`: consumes the output of the former task and create vms for the nodes of the cluster. It generates an inventory of nodes.
- `inventory tasks` : tasks that will insert the oVirt VMs from former tasks into the inventory, so you don't need to specify it manually in the inventory.

## Role Variables

For documentation on virtual machine profile options, see the [oVirt Ansible VM-Infra Documentation](https://github.com/oVirt/ovirt-ansible-vm-infra)

| Name                      | Default value |                                                                                         |
|---------------------------|---------------|-----------------------------------------------------------------------------------------|
| openshift_ovirt_all_in_one  | false    | When true, creates an all in one inventory entries from the first master vm |
| openshift_ovirt_vm_profile  | See below.    | Dictionary of dictionaries providing common VM parameters for virtual machine creation. |
| openshift_ovirt_vm_manifest | See below.    | List of dictionaries specifying node base name, count, and which of the above profiles to apply. The default creates three master nodes, three infrastructure nodes, one application node, and a load balancer. |

The `openshift_ovirt_vm_manifest` variable can contain following attributes

| Name      | Type | Default value |                                                                                                                 |
|-----------|------|---------------|-----------------------------------------------------------------------------------------------------------------|
| nics      | Dict | UNDEF         | Coresoponds to 'nics' section in oVirt.vm-infra module. Lets you set a nic `name`, 'network`, `interface`, and `mac_address`. |
| nic_mode  | Dict | UNDEF         | If you define this variable means that the interface on the VM will have static address instead of dynamic one. |
| empty_hostname  | Bool | True   | If True, the VM's Hostname will remain empty in cloud-init, and will relays the VM's hostname on DHCP name. |
| ovirt_admin  | Bool | True   | If False, the role will not try to add tags to the created vms and also avoid to get into affinity groups. This way the role could be executed without admin rights |

Below `nic_mode` we can find this other parameters

| Name            |  Type  | Default value |                                          |
|-----------------|--------|---------------|------------------------------------------|
| nic_ip_address  | String | UNDEF         | Static ipaddress for vm interface.       |
| nic_netmask     | String | UNDEF         | Static Netmask for vm interface .        |
| nic_gateway     | String | UNDEF         | Static Gateway address for vm interface. |
| nic_on_boot     | Bool   | True          | The interface will be up on boot.        |
| nic_name        | String | 'eth0'        | The Interface name for the vm.           |
| dns_servers     | String | UNDEF         | The DNS set on the VM.                   |


`nics` parameters reffer to the oVirt.vm-infra ['nics' role parameters](https://github.com/oVirt/ovirt-ansible-vm-infra/blob/master/README.md):

| Name               | Default value  |                                              |
|--------------------|----------------|----------------------------------------------|
| name               | UNDEF          | The name of the network interface.           |
| interface          | UNDEF          | Type of the network interface.               |
| mac_address        | UNDEF          | Custom MAC address of the network interface, by default it's obtained from MAC pool. |
| network            | UNDEF          | Logical network which the VM network interface should use. If network is not specified, then Empty network is used. |
| profile            | UNDEF          | Virtual network interface profile to be attached to VM network interface. |



## Examples

### Manifest
- **openshift_ovirt_vm_profile**

```
openshift_ovirt_vm_profile:
  master:
    cluster: "{{ openshift_ovirt_cluster }}"
    template: "{{ ovirt_template_name }}"
    memory: 16GiB
    cores: 2
    high_availability: true
    disks:
    - size: 15GiB
      storage_domain: "{{ openshift_ovirt_data_store }}"
      name: docker_disk
      interface: virtio
    - size: 30GiB
      storage_domain: "{{ openshift_ovirt_data_store }}"
      name: localvol_disk
      interface: virtio
    - size: 25GiB
      storage_domain: "{{ openshift_ovirt_data_store }}"
      name: etcd_disk
      interface: virtio
    state: running
  node:
    cluster: "{{ openshift_ovirt_cluster }}"
    template: "{{ ovirt_template_name }}"
    memory: 8GiB
    cores: 2
    high_availability: true
    disks:
    - size: 15GiB
      storage_domain: "{{ openshift_ovirt_data_store }}"
      name: docker_disk
      interface: virtio
    - size: 30GiB
      storage_domain: "{{ openshift_ovirt_data_store }}"
      name: localvol_disk
      interface: virtio
    state: running
```

- **openshift_ovirt_vm_manifest**
```
openshift_ovirt_vm_manifest:
- name: 'master'
  count: 3
- name: 'infra'
  count: 2
  profile: 'node'
- name: 'compute'
  count: 9
  profile: 'node'


- **openshift_ovirt_vm_manifest with static IPs**
```yaml
openshift_ovirt_vm_manifest:
#######################################
# Multiple Node Static Ip addresses
#######################################
  - name: 'master'
    count: 3
    profile: 'master'
    empty_hostname: True
    nic_mode:
      # This must fit the same name as this kind of vms. (e.g) if the name is test, this must be test0
      master0:
        nic_ip_address: '192.168.123.160'
        nic_netmask: '255.255.255.0'
        nic_gateway: '192.168.123.1'
        nic_on_boot: True
        nic_name: 'eth0'
        dns_servers: "192.168.1.100"
      master1:
        nic_ip_address: '192.168.123.161'
        nic_netmask: '255.255.255.0'
        nic_gateway: '192.168.123.1'
        nic_on_boot: True
        nic_name: 'nic0'
        dns_servers: "192.168.1.100"
      master2:
        nic_ip_address: '192.168.123.162'
        nic_netmask: '255.255.255.0'
        nic_gateway: '192.168.123.1'
        nic_on_boot: True
        dns_servers: "192.168.1.100"
  - name: 'infra'
    count: 2
    profile: 'node'
    nic_mode:
      infra0:
        nic_ip_address: '192.168.123.163'
        nic_netmask: '255.255.255.0'
        nic_gateway: '192.168.123.1'
        nic_on_boot: True
        dns_servers: "192.168.1.100"
      infra1:
        nic_ip_address: '192.168.123.164'
        nic_netmask: '255.255.255.0'
        nic_gateway: '192.168.123.1'
        nic_on_boot: True
        dns_servers: "192.168.1.100"

################################################
# Multiple/Single Node Dynamic Ip addresses
################################################
  - name: 'compute'
    count: 2
    profile: 'node'

######################################
# Single Node Static Ip addresses
######################################
  - name: 'lb'
    count: 1
    profile: 'node_vm'
    nic_mode:
      lb:
        nic_ip_address: '192.168.123.170'
        nic_netmask: '255.255.255.0'
        nic_gateway: '192.168.123.1'
        dns_servers: "192.168.1.100"
```

### Setting Mac addresses for 3 masters

```yaml
openshift_ovirt_vm_manifest:
  - name: 'master'
    count: 3
    profile: 'master'
    nics:
      - mac_address: 56:3f:24:a7:00:10
      - mac_address: 56:3f:24:a7:00:20
      - mac_address: 56:3f:24:a7:00:30
```
### Playbook

```
---
- name: Deploy OKD on oVirt from zero to working state
  hosts: localhost
  connection: local
  gather_facts: false

  pre_tasks:
    - name: Log in to oVirt
      ovirt_auth:
        url: "{{ engine_url }}"
        username: "{{ engine_user }}"
        password: "{{ engine_password }}"
        ca_file: "{{ engine_cafile | default(omit) }}"
        insecure: "{{ engine_insecure | default(true) }}"
      tags:
        - always

  tasks:
    - import_role:
        name: openshift_ovirt

- import_playbook: /home/rgolan/src/openshift-ansible/playbooks/prerequisites.yml
- import_playbook: /home/rgolan/src/openshift-ansible/playbooks/openshift-node/network_manager.yml
- import_playbook: /home/rgolan/src/openshift-ansible/playbooks/deploy_cluster.yml

  post_tasks:
    - name: Logout from oVirt
      ovirt_auth:
        state: absent
        ovirt_auth: "{{ ovirt_auth }}"
      tags:
        - always
```

License
-------

Apache License, Version 2.0
