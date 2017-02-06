OpenShift Excluder
================

Manages the excluder packages which add yum and dnf exclusions ensuring that
the packages we care about are not inadvertantly updated. See
https://github.com/openshift/origin/tree/master/contrib/excluder

Requirements
------------
openshift_facts


Facts
-----

| Name                       | Default Value | Description                            |
-----------------------------|---------------|----------------------------------------|
| docker_excluder_enabled | none          | Records the status of docker excluder |
| openshift_excluder_enabled | none | Records the status of the openshift excluder |

Role Variables
--------------
None

Dependencies
------------

Example Playbook
----------------


TODO
----
It should be possible to manage the two excluders independently though that's not a hard requirement. However it should be done to manage docker on RHEL Containerized hosts.

License
-------

Apache License, Version 2.0

Author Information
------------------

Scott Dodson (sdodson@redhat.com)
