Role Name
=========

Configures an etcd cluster for an arbitrary number of hosts

Requirements
------------

This role assumes it's being deployed on a RHEL/Fedora based host with package
named 'etcd' available via yum.

Role Variables
--------------

TODO

Dependencies
------------

None

Example Playbook
----------------

    - hosts: etcd
      roles:
         - { etcd }

License
-------

MIT

Author Information
------------------

Scott Dodson <sdodson@redhat.com>
Adapted from https://github.com/retr0h/ansible-etcd for use on RHEL/Fedora. We
should at some point submit a PR to merge this with that module.
