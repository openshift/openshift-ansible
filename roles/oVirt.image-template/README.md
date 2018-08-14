oVirt Image Template
====================

The `oVirt.image-template` role creates a template from external image. Currently the disk can be an image in Glance external provider or QCOW2 image.

Requirements
------------

 * Ansible version 2.5 or higher.
 * Python SDK version 4.2 or higher.
 * oVirt has to be 4.1 or higher and [ovirt-imageio] must be installed and running.
 * CA certificate of oVirt engine. The path to CA certificate must be specified in the `ovirt_ca` variable.

Role Variables
--------------

| Name               | Default value         |                            |
|--------------------|-----------------------|----------------------------|
| ovirt_qcow_url           | UNDEF (mandatory if glance is not used)                | The URL of the QCOW2 image. |
| ovirt_image_path         | /tmp/                 | Path where the QCOW2 image will be downloaded to. If directory the base name of the URL on the remote server will be used. |
| ovirt_image_checksum     | UNDEF                 | If a checksum is defined, the digest of the destination file will be calculated after it is downloaded to ensure its integrity and verify that the transfer completed successfully. Format: <algorithm>:<checksum>, e.g. checksum="sha256:D98291AC[...]B6DC7B97". |
| ovirt_image_cache_download | true                | When set to false will delete ovirt_image_path at the start and end of execution |
| ovirt_template_cluster   | Default               | Name of the cluster where template must be created. |
| ovirt_template_name      | mytemplate            | Name of the template. |
| ovirt_template_memory    | 2GiB                  | Amount of memory assigned to the template. |
| ovirt_template_memory_guaranteed    | UNDEF      | Amount of minimal guaranteed memory of the Virtual Machine |
| ovirt_template_memory_max    | UNDEF             | Upper bound of virtual machine memory up to which memory hot-plug can be performed. |
| ovirt_template_cpu       | 1                     | Number of CPUs assigned to the template.  |
| ovirt_template_disk_storage | UNDEF              | Name of the data storage domain where the disk must be created. If not specified, the data storage domain is selected automatically. |
| ovirt_template_disk_size | 10GiB                 | The size of the template disk.  |
| ovirt_template_disk_name | UNDEF                 | The name of template disk.  |
| ovirt_template_disk_format | UNDEF               | Format of the template disk.  |
| ovirt_template_disk_interface | virtio           | Interface of the template disk. |
| ovirt_template_timeout   | 600                   | Amount of time to wait for the template to be created. |
| ovirt_template_type      | UNDEF                 | The type of the template: desktop, server or high_performance (for qcow2 based templates only) |
| ovirt_template_nics      | {name: nic1, profile_name: ovirtmgmt, interface: virtio} | List of dictionaries that specify the NICs of template. |
| ovirt_template_operating_system | UNDEF | Operating system of the template like: other, rhel_7x64, debian_7, see others in ovirt_template module. |
| ovirt_glance_image_provider        | UNDEF (mandatory if ovirt_qcow_url is not used)            | Name of the glance image provider.                    |
| ovirt_glance_image            | UNDEF (mandatory if ovirt_qcow_url is not used)               | This parameter specifies the name of disk in glance provider to be imported as template. |


Dependencies
------------

No.

Example Playbook
----------------

```yaml
---
- name: Create a template from qcow
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    ovirt_engine_url: https://ovirt-engine.example.com/ovirt-engine/api
    ovirt_engine_user: admin@internal
    ovirt_engine_password: 123456
    ovirt_engine_cafile: /etc/pki/ovirt-engine/ca.pem

    ovirt_qcow_url: https://cloud.centos.org/centos/7/images/CentOS-7-x86_64-GenericCloud.qcow2
    ovirt_template_cluster: production
    ovirt_template_name: centos7_template
    ovirt_template_memory: 4GiB
    ovirt_template_cpu: 2
    ovirt_template_disk_size: 10GiB
    ovirt_template_disk_storage: mydata

  roles:
    - oVirt.image-template


- name: Create a template from a disk stored in glance
  hosts: localhost
  connection: local
  gather_facts: false

  vars:
    ovirt_engine_url: https://ovirt-engine.example.com/ovirt-engine/api
    ovirt_engine_user: admin@internal
    ovirt_engine_password: 123456
    ovirt_engine_cafile: /etc/pki/ovirt-engine/ca.pem

    ovirt_glance_image_provider: qe-infra-glance
    ovirt_glance_image: rhel7.4_ovirt4.2_guest_disk
    ovirt_template_cluster: production
    ovirt_template_name: centos7_template
    ovirt_template_memory: 4GiB
    ovirt_template_cpu: 2
    ovirt_template_disk_size: 10GiB
    ovirt_template_disk_storage: mydata

  roles:
    - ovirt-image-template
```

[![asciicast](https://asciinema.org/a/111478.png)](https://asciinema.org/a/111478)

License
-------

Apache License 2.0

[ovirt-imageio]: http://www.ovirt.org/develop/release-management/features/storage/image-upload/
