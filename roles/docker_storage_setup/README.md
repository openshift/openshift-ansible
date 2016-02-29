docker_storage_setup
=========
This role coverts docker to go from loopback to direct-lvm (the Red Hat recommended way to run docker).

It requires the block device to be already provisioned and attached to the host.

  Notes:
  * This is NOT idempotent. Conversion needs to be done for it to be idempotent
  * This will remove /var/lib/docker!
  * You will need to re-deploy docker images

Configure docker_storage_setup
------------

None

Role Variables
--------------

dss_docker_device: defaults to /dev/xvdb

Dependencies
------------

None

Example Playbook
----------------

    - hosts: servers
      roles:
         - { role/docker_storage_setup, dss_docker_device: '/dev/xvdb' }

License
-------

ASL 2.0

Author Information
------------------

OpenShift operations, Red Hat, Inc
