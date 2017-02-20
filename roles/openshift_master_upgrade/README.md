Role Name
=========

Role responsible for a single master upgrade.
It is expected a master is functioning and a part of an OpenShift cluster.

Requirements
------------

TODO

Role Variables
--------------
General vars

| Name                           | Default value         |                                                        |
|--------------------------------|-----------------------|--------------------------------------------------------|
| openshift_deployment_type      |                       | Inventory var                                          |
| openshift_image_tag            |                       | Set by openshift_version role                          |
| openshift_pkg_version          |                       | Set by openshift_version role                          |
| openshift_upgrade_min          |                       |                                                        |
| master_config_hook             |                       | Set by upgrade play                                    |

From openshift.common:

| Name                                  |  Default Value      |                     |
|---------------------------------------|---------------------|---------------------|
| openshift.common.config_base          |                     |                     |
| openshift.common.hostname             |                     |                     |
| openshift.common.http_proxy           |                     |                     |
| openshift.common.is_atomic            |                     |                     |
| openshift.common.is_containerized     |                     |                     |
| openshift.common.portal_net           |                     |                     |
| openshift.common.rolling_restart_mode |                     |                     |
| openshift.common.service_type         |                     |                     |
| openshift.common.use_openshift_sdn    |                     |                     |

From openshift.master:

| Name                                  |  Default Value      |                     |
|---------------------------------------|---------------------|---------------------|
| openshift.master.api_port             |                     |                     |
| openshift_master_ha                   |                     |                     |
| openshift_master_scheduler_predicates |                     |                     |
| openshift_master_scheduler_priorities |                     |                     |
| openshift_master_upgrade_hook         |                     |                     |
| openshift_master_upgrade_post_hook    |                     |                     |
| openshift_master_upgrade_pre_hook     |                     |                     |

From openshift.node:

| Name                               |  Default Value      |                     |
|------------------------------------|---------------------|---------------------|
| openshift.node.debug_level         |                     |                     |
| openshift.node.node_image          |                     |                     |
| openshift.node.ovs_image           |                     |                     |

Dependencies
------------
openshift_master_facts
openshift_version
openshift_common

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

```
- name: Upgrade master
  hosts: oo_masters_to_config
  vars:
    openshift_master_ha: "{{ groups.oo_masters_to_config | length > 1 }}"
  serial: 1
  roles:
  - openshift_facts
  - openshift_master_upgrade
  post_tasks:
  - set_fact:
      master_update_complete: True
```

License
-------

Apache License, Version 2.0

Author Information
------------------

TODO
