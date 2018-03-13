Docker
=========

Ensures docker package or system container is installed, and optionally raises timeout for systemd-udevd.service to 5 minutes.

container-daemon.json items may be found at https://docs.docker.com/engine/reference/commandline/dockerd/#daemon-configuration-file

Requirements
------------

Ansible 2.2

Role Variables
--------------

docker_conf_dir: location of the Docker configuration directory
docker_systemd_dir location of the systemd directory for Docker
docker_udev_workaround: raises udevd timeout to 5 minutes (https://bugzilla.redhat.com/show_bug.cgi?id=1272446)
udevw_udevd_dir: location of systemd config for systemd-udevd.service

Dependencies
------------

Depends on the os_firewall role.

Example Playbook
----------------

    - hosts: servers
      roles:
      - role: docker
        docker_udev_workaround: "true"
        docker_use_system_container: False

License
-------

ASL 2.0

Author Information
------------------

OpenShift operations, Red Hat, Inc
