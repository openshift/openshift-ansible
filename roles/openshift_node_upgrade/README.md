OpenShift/Atomic Enterprise Node upgrade
=========

Role responsible for a single node upgrade.
It is expected a node is functioning and a part of an OpenShift cluster.

Requirements
------------

TODO

Role Variables
--------------
From this role:

| Name                           | Default value         |                                                        |
|--------------------------------|-----------------------|--------------------------------------------------------|
| deployment_type                |                       | Inventory var                                          |
| docker_upgrade_nuke_images     |                       | Optional inventory var                                 |
| docker_version                 |                       | Optional inventory var                                 |
| l_docker_upgrade               |                       |                                                        |
| node_config_hook               |                       |                                                        |
| openshift.docker.gte_1_10      |                       |                                                        |
| openshift_image_tag            |                       | Set by openshift_version role                          |
| openshift_pkg_version          |                       | Set by openshift_version role                          |
| openshift_release              |                       | Set by openshift_version role                          |
| skip_docker_restart            |                       |                                                        |
| openshift_cloudprovider_kind   |                       |                                                        |

From openshift.common:

| Name                               |  Default Value      |                     |
|------------------------------------|---------------------|---------------------|
| openshift.common.config_base       |---------------------|---------------------|
| openshift.common.data_dir          |---------------------|---------------------|
| openshift.common.hostname          |---------------------|---------------------|
| openshift.common.http_proxy        |---------------------|---------------------|
| openshift.common.is_atomic         |---------------------|---------------------|
| openshift.common.is_containerized  |---------------------|---------------------|
| openshift.common.portal_net        |---------------------|---------------------|
| openshift.common.service_type      |---------------------|---------------------|
| openshift.common.use_openshift_sdn |---------------------|---------------------|

From openshift.master:

| Name                               |  Default Value      |                     |
|------------------------------------|---------------------|---------------------|
| openshift.master.api_port          |---------------------|---------------------|

From openshift.node:

| Name                               |  Default Value      |                     |
|------------------------------------|---------------------|---------------------|
| openshift.node.debug_level         |---------------------|---------------------|
| openshift.node.node_image          |---------------------|---------------------|
| openshift.node.ovs_image           |---------------------|---------------------|


Dependencies
------------
openshift_common

TODO

Example Playbook
----------------

Including an example of how to use your role (for instance, with variables passed in as parameters) is always nice for users too:

```
---
- name: Upgrade nodes
  hosts: oo_nodes_to_upgrade
  serial: 1
  any_errors_fatal: true

  pre_tasks:
  - name: Mark unschedulable
    command: >
      {{ hostvars[groups.oo_first_master.0].openshift.common.client_binary }} adm manage-node {{ openshift.node.nodename | lower }} --schedulable=false
    delegate_to: "{{ groups.oo_first_master.0 }}"

  - name: Drain Node for Kubelet upgrade
    command: >
      {{ hostvars[groups.oo_first_master.0].openshift.common.admin_binary }} drain {{ openshift.node.nodename | lower }} --force --delete-local-data --ignore-daemonsets
    delegate_to: "{{ groups.oo_first_master.0 }}"

  roles:
  - openshift_facts
  - docker
  - openshift_node_dnsmasq
  - openshift_node_upgrade

  post_tasks:
  - name: Set node schedulability
    command: >
      {{ hostvars[groups.oo_first_master.0].openshift.common.client_binary }} adm manage-node {{ openshift.node.nodename | lower }} --schedulable=true
    delegate_to: "{{ groups.oo_first_master.0 }}"
```

License
-------

Apache License, Version 2.0

Author Information
------------------

TODO
