Updated modules
===============

Here is list of updated modules:

1. ovirt_templates.py

- Support `memory`, `memory_guaranteed`, `memory_max` and `operating_system`
  which will be added in Ansible 2.6. So it can be removed once 2.6 is
  released. Related change was merged here: [PR](https://github.com/ansible/ansible/pull/38211)

- Previously we searched by name, but it's not enough as template could have
  same names in different clusters, so we improve the search to search also
  by cluster name. [PR](https://github.com/ansible/ansible/pull/40934)
