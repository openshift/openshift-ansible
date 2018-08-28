OpenShift oVirt
=============

OpenShift Provisioned on Red Hat Virtualization and oVirt

Role Tasks
----------

* `build_vm_list.yml`: Creates a list of virtual machine definitions and
  affinity groups based on a simple manifest (below)

Role Variables
--------------

For documentation on virtual machine profile options, see the [oVirt Ansible VM-Infra Documentation](https://github.com/oVirt/ovirt-ansible-vm-infra)

| Name                      | Default value |                                                                                         |
|---------------------------|---------------|-----------------------------------------------------------------------------------------|
| openshift_ovirt_vm_profile  | See below.    | Dictionary of dictionaries providing common VM parameters for virtual machine creation. |
| openshift_ovirt_vm_manifest | See below.    | List of dictionaries specifying node base name, count, and which of the above profiles to apply. The default creates three master nodes, three infrastructure nodes, one application node, and a load balancer. |

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

```
openshift_ovirt_vm_manifest:
- name: 'master'
  count: 3
  profile: 'master'
- name: 'infra'
  count: 3
  profile: 'node'
- name: 'compute'
  count: 1
  profile: 'node'
- name: 'lb'
  count: 1
  profile: 'node'
```

Example Playbook
----------------

License
-------

Apache License, Version 2.0
