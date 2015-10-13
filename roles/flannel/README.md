Role Name
=========

Configure flannel on openshift nodes

Requirements
------------

This role assumes it's being deployed on a RHEL/Fedora based host with package
named 'flannel' available via yum, in version superior to 0.3.

Role Variables
--------------

TODO

Dependencies
------------

openshift_facts

Example Playbook
----------------

    - hosts: openshift_node
      roles:
         - { flannel }

License
-------

Apache License, Version 2.0

Author Information
------------------

Sylvain Baubeau <sbaubeau@redhat.com>
