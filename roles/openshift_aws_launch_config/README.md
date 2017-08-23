openshift_aws_launch_config
=========

Ansible role to create an AWS launch config for a scale group.

This includes the AMI, volumes, user_data, etc.

Requirements
------------

Ansible Modules:


Role Variables
--------------
- r_openshift_aws_launch_config_name: "{{ launch_config_name }}"
- r_openshift_aws_launch_config_clusterid: "{{ clusterid }}"
- r_openshift_aws_launch_config_region: "{{ region }}"
- r_openshift_aws_launch_config: "{{ node_group_config }}"
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
- r_openshift_aws_launch_config_type: compute
- r_openshift_aws_launch_config_custom_image: ami-xxxxx
- r_openshift_aws_launch_config_bootstrap_token: <string of kubeconfig>

Dependencies
------------


Example Playbook
----------------
```yaml
  - name: create compute nodes config
    include_role:
      name: openshift_aws_launch_config
    vars:
      r_openshift_aws_launch_config_name: "{{ launch_config_name }}"
      r_openshift_aws_launch_config_clusterid: "{{ clusterid }}"
      r_openshift_aws_launch_config_region: "{{ region }}"
      r_openshift_aws_launch_config: "{{ node_group_config }}"
      r_openshift_aws_launch_config_type: compute
      r_openshift_aws_launch_config_custom_image: ami-1234
      r_openshift_aws_launch_config_bootstrap_token: abcd
```

License
-------

Apache 2.0

Author Information
------------------

Openshift
