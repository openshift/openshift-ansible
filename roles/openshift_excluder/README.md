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
| enable_docker_excluder     | enable_excluders | Enable docker excluder. If not set, the docker excluder is ignored. |
| enable_openshift_excluder  | enable_excluders | Enable openshift excluder. If not set, the openshift excluder is ignored. |
| enable_excluders           | None             | Enable all excluders

Role Variables
--------------
None

Dependencies
------------

Tasks to include
----------------

- exclude: enable excluders (assuming excluders are installed)
- unexclude: disable excluders (assuming excluders are installed)
- install: install excluders (installation is followed by excluder enabling)
- enable: enable excluders (optionally with installation step)
- disabled: disable excluders (optionally with installation and status step, the status check that can override which excluder gets enabled/disabled)
- status: determine status of excluders

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
