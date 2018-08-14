OpenShift RHV
=============

OpenShift Provisioned on Red Hat Virtualization and oVirt

Optional Requirements
---------------------

* External DNS server to provide name resolution to nodes and applications. See the [OpenShift Installation Documentation](https://docs.openshift.com/container-platform/3.9/install_config/install/prerequisites.html#prereq-dns) for details.
* dnspython (If using the nsupdate code)

Role Tasks
----------

* `build_vm_list.yml`: Creates a list of virtual machine definitions and
  affinity groups based on a simple manifest (below)
* `generate_hostfile.yml`: Creates a file in the style of `/etc/hosts` based on inventory
* `generate_nsupdate.yml`: Creates nsupdate entries for entry via the nsupdate module.
  Requires inventory with FQDN names and IP addresses in `ansible_host` field
* `hosts_from_dns.yml`: Creates inventory entries with IP addresses in the
  `ansible_host` field as required by 

Role Variables
--------------

For documentation on virtual machine profile options, see the [oVirt Ansible VM-Infra Documentation](https://github.com/oVirt/ovirt-ansible-vm-infra)

| Name                      | Default value |                                                                                         |
|---------------------------|---------------|-----------------------------------------------------------------------------------------|
| openshift_rhv_vm_profile  | See below.    | Dictionary of dictionaries providing common VM parameters for virtual machine creation. |
| openshift_rhv_vm_manifest | See below.    | List of dictionaries specifying node base name, count, and which of the above profiles to apply. The default creates three master nodes, three infrastructure nodes, three application nodes, and a load balancer. |

```
openshift_rhv_vm_profile:
  master:
    cluster: "{{ openshift_rhv_cluster }}"
    template: "{{ ovirt_template_name }}"
    memory: 16GiB
    cores: 2
    high_availability: true
    disks:
    - size: 15GiB
      storage_domain: "{{ openshift_rhv_data_store }}"
      name: docker_disk
      interface: virtio
    - size: 30GiB
      storage_domain: "{{ openshift_rhv_data_store }}"
      name: localvol_disk
      interface: virtio
    - size: 25GiB
      storage_domain: "{{ openshift_rhv_data_store }}"
      name: etcd_disk
      interface: virtio
    state: running
  node:
    cluster: "{{ openshift_rhv_cluster }}"
    template: "{{ ovirt_template_name }}"
    memory: 8GiB
    cores: 2
    high_availability: true
    disks:
    - size: 15GiB
      storage_domain: "{{ openshift_rhv_data_store }}"
      name: docker_disk
      interface: virtio
    - size: 30GiB
      storage_domain: "{{ openshift_rhv_data_store }}"
      name: localvol_disk
      interface: virtio
    state: running
```

```
openshift_rhv_vm_manifest:
- name: 'master'
  count: 3
  profile: 'master'
- name: 'infra'
  count: 3
  profile: 'node'
- name: 'compute'
  count: 3
  profile: 'node'
- name: 'lb'
  count: 1
  profile: 'node'
```

To automatically update DNS using `nsupdate`, ensure the following variables are defined:

- `app_dns_prefix`: Part of the default subdomain for wildcard entries. e.g. `apps` in `*.apps.example.com`.
- `public_hosted_zone`: The default subdomain added to the end of most entries, e.g. `example.com`.
- `openshift_rhv_nsupdate_server`: Server name to send nsupdate updates.
- `openshift_rhv_nsupdate_key`: Dictionary made up of parameters found in the rndc key of the nsupdate server.

```
openshift_rhv_nsupdate_server: localhost
openshift_rhv_nsupdate_key:
  name: rndc-key
  secret: 'XYXYXYXYXYXYXYXYXYXY+h=='
  algorithm: hmac-md5
```

Example Playbook
----------------

```
- name: Create dns nsupdate or hosts files for admin use
  hosts: localhost
  tasks:
  - import_role:
      name: oVirt.vm-infra
      tasks_from: create_inventory.yml
  - import_role:
      name: openshift_rhv
      tasks_from: generate_dns.yml
```

License
-------

Apache License, Version 2.0
