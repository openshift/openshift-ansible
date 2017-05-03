Docker
=========

Adds specified certificate authorities to system ca-trust.

Requirements
------------

None

Role Variables
--------------

docker_ca_certs: List of remote ca certificate paths.

Dependencies
------------

None

Example Playbook
----------------

    - hosts: servers
      roles:
      - role: docker_ca_trust
        docker_ca_certs:
	- /etc/origin/node/ca.crt

License
-------

ASL 2.0

Author Information
------------------

OpenShift operations, Red Hat, Inc
