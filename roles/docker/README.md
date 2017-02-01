Docker
=========

Ensures docker package is installed, and optionally raises timeout for systemd-udevd.service to 5 minutes.

Requirements
------------

Ansible 2.2

Role Variables
--------------

udevw_udevd_dir: location of systemd config for systemd-udevd.service
docker_udev_workaround: raises udevd timeout to 5 minutes (https://bugzilla.redhat.com/show_bug.cgi?id=1272446)

Dependencies
------------

Depends on the os_firewall role.

Example Playbook
----------------

    - hosts: servers
      roles:
      - role: docker
        docker_udev_workaround: "true"

License
-------

ASL 2.0

Author Information
------------------

OpenShift operations, Red Hat, Inc
