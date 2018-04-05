Role Name
=========

Performs application idling to conserve resources. Accepts a list of projects to
exclude from idling.

See [documentation](https://docs.openshift.org/latest/admin_guide/idling_applications.html).

Requirements
------------

* Ansible 2.2

Role Variables
--------------

| Name                                         | Default value | Description                                                                  |
|----------------------------------------------|---------------|------------------------------------------------------------------------------|
| openshift_idling_excluded_projects           |               | List of projects to exclude from idling. Additional infrastructure projects are excluded by default: default, kube-system, openshift-web-console
| openshift_idling_dry_run                     | False         | Print services that would be idled but do not idle

Dependencies
------------

openshift_facts

Example Playbook
----------------

    - hosts: oo_first_master
      vars:
        openshift_idling_excluded_projects:
          - myproject
      roles:
         - openshift_idling

License
-------

Apache License, Version 2.0
