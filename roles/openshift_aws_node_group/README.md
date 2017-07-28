openshift_aws_node_group
=========

Ansible role to create an aws node group.

This includes the security group, launch config, and scale group.

Requirements
------------

Ansible Modules:


Role Variables
--------------
```yaml
- r_openshift_aws_node_group_name: myscalegroup
- r_openshift_aws_node_group_clusterid: myclusterid
- r_openshift_aws_node_group_region: us-east-1
- r_openshift_aws_node_group_lc_name: launch_config
- r_openshift_aws_node_group_type: master|infra|compute
- r_openshift_aws_node_group_config: "{{ node_group_config }}"
```yaml
master:
  instance_type: m4.xlarge
  ami: ami-cdeec8b6  # if using an encrypted AMI this will be replaced
  volumes:
  - device_name: /dev/sdb
    volume_size: 100
    device_type: gp2
    delete_on_termination: False
  health_check:
    period: 60
    type: EC2
  min_size: 3
  max_size: 3
  desired_size: 3
  tags:
    host-type: master
    sub-host-type: default
  wait_for_instances: True
```
- r_openshift_aws_node_group_subnet_name: "{{ subnet_name }}"

```yaml
us-east-1a  # name of subnet
```

Dependencies
------------


Example Playbook
----------------
```yaml
  - name: "create {{ openshift_build_node_type }} node groups"
    include_role:
      name: openshift_aws_node_group
    vars:
      r_openshift_aws_node_group_name: "{{ clusterid }} openshift compute"
      r_openshift_aws_node_group_lc_name: "{{ launch_config_name }}"
      r_openshift_aws_node_group_clusterid: "{{ clusterid }}"
      r_openshift_aws_node_group_region: "{{ region }}"
      r_openshift_aws_node_group_config: "{{ node_group_config }}"
      r_openshift_aws_node_group_type: compute
      r_openshift_aws_node_group_subnet_name: "{{ subnet_name }}"
```

License
-------

Apache 2.0

Author Information
------------------

Openshift
