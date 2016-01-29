lib_dyn
=========

A role containing the dyn_record module for managing DNS records through Dyn's
API

Requirements
------------

The module requires the `dyn` python module for interacting with the Dyn API.
https://github.com/dyninc/dyn-python

Example Playbook
----------------

To make sure the `dyn_record` module is available for use include the role
before it is used.

    - hosts: servers
      roles:
         - lib_dyn

License
-------

Apache

