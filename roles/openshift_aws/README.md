openshift_aws
==================================

Provision AWS infrastructure helpers.

Requirements
------------

* Ansible 2.3
* Boto

Role Variables
--------------

From this role:

| Name                                              | Default value
|---------------------------------------------------|-----------------------
| openshift_aws_clusterid                           | default
| openshift_aws_elb_scheme                          | internet-facing
| openshift_aws_launch_config_bootstrap_token       | ''
| openshift_aws_node_group_config                   | {'master': {'ami': '{{ openshift_aws_ami }}', 'health_check': {'type': 'EC2', 'period': 60}, 'volumes': '{{ openshift_aws_node_group_config_master_volumes }}', 'tags': {'host-type': 'master', 'sub-host-type': 'default'}, 'min_size': 3, 'instance_type': 'm4.xlarge', 'desired_size': 3, 'wait_for_instances': True, 'max_size': 3}, 'tags': '{{ openshift_aws_node_group_config_tags }}', 'compute': {'ami': '{{ openshift_aws_ami }}', 'health_check': {'type': 'EC2', 'period': 60}, 'volumes': '{{ openshift_aws_node_group_config_node_volumes }}', 'tags': {'host-type': 'node', 'sub-host-type': 'compute'}, 'min_size': 3, 'instance_type': 'm4.xlarge', 'desired_size': 3, 'max_size': 100}, 'infra': {'ami': '{{ openshift_aws_ami }}', 'health_check': {'type': 'EC2', 'period': 60}, 'volumes': '{{ openshift_aws_node_group_config_node_volumes }}', 'tags': {'host-type': 'node', 'sub-host-type': 'infra'}, 'min_size': 2, 'instance_type': 'm4.xlarge', 'desired_size': 2, 'max_size': 20}}
| openshift_aws_ami_copy_wait                       | False
| openshift_aws_users                               | []
| openshift_aws_launch_config_name                  | {{ openshift_aws_clusterid }}-{{ openshift_aws_node_group_type }}
| openshift_aws_node_group_type                     | master
| openshift_aws_elb_cert_arn                        | ''
| openshift_aws_kubernetes_cluster_status           | owned
| openshift_aws_s3_mode                             | create
| openshift_aws_vpc                                 | {'subnets': {'us-east-1': [{'cidr': '172.31.48.0/20', 'az': 'us-east-1c'}, {'cidr': '172.31.32.0/20', 'az': 'us-east-1e'}, {'cidr': '172.31.16.0/20', 'az': 'us-east-1a'}]}, 'cidr': '172.31.0.0/16', 'name': '{{ openshift_aws_vpc_name }}'}
| openshift_aws_create_ssh_keys                     | False
| openshift_aws_iam_kms_alias                       | alias/{{ openshift_aws_clusterid }}_kms
| openshift_aws_use_custom_ami                      | False
| openshift_aws_ami_copy_src_region                 | {{ openshift_aws_region }}
| openshift_aws_s3_bucket_name                      | {{ openshift_aws_clusterid }}
| openshift_aws_elb_health_check                    | {'response_timeout': 5, 'ping_port': 443, 'ping_protocol': 'tcp', 'interval': 30, 'healthy_threshold': 2, 'unhealthy_threshold': 2}
| openshift_aws_node_security_groups                | {'default': {'rules': [{'to_port': 22, 'from_port': 22, 'cidr_ip': '0.0.0.0/0', 'proto': 'tcp'}, {'to_port': 'all', 'from_port': 'all', 'proto': 'all', 'group_name': '{{ openshift_aws_clusterid }}'}], 'name': '{{ openshift_aws_clusterid }}', 'desc': '{{ openshift_aws_clusterid }} default'}, 'master': {'rules': [{'to_port': 80, 'from_port': 80, 'cidr_ip': '0.0.0.0/0', 'proto': 'tcp'}, {'to_port': 443, 'from_port': 443, 'cidr_ip': '0.0.0.0/0', 'proto': 'tcp'}], 'name': '{{ openshift_aws_clusterid }}_master', 'desc': '{{ openshift_aws_clusterid }} master instances'}, 'compute': {'name': '{{ openshift_aws_clusterid }}_compute', 'desc': '{{ openshift_aws_clusterid }} compute node instances'}, 'etcd': {'name': '{{ openshift_aws_clusterid }}_etcd', 'desc': '{{ openshift_aws_clusterid }} etcd instances'}, 'infra': {'rules': [{'to_port': 80, 'from_port': 80, 'cidr_ip': '0.0.0.0/0', 'proto': 'tcp'}, {'to_port': 443, 'from_port': 443, 'cidr_ip': '0.0.0.0/0', 'proto': 'tcp'}, {'to_port': 32000, 'from_port': 30000, 'cidr_ip': '0.0.0.0/0', 'proto': 'tcp'}], 'name': '{{ openshift_aws_clusterid }}_infra', 'desc': '{{ openshift_aws_clusterid }} infra node instances'}}
| openshift_aws_elb_security_groups                 | ['{{ openshift_aws_clusterid }}', '{{ openshift_aws_clusterid }}_{{ openshift_aws_node_group_type }}']
| openshift_aws_vpc_tags                            | {'Name': '{{ openshift_aws_vpc_name }}'}
| openshift_aws_create_security_groups              | False
| openshift_aws_create_iam_cert                     | False
| openshift_aws_create_scale_group                  | True
| openshift_aws_ami_encrypt                         | False
| openshift_aws_node_group_config_node_volumes      | [{'volume_size': 100, 'delete_on_termination': True, 'device_type': 'gp2', 'device_name': '/dev/sdb'}]
| openshift_aws_elb_instance_filter                 | {'tag:host-type': '{{ openshift_aws_node_group_type }}', 'tag:clusterid': '{{ openshift_aws_clusterid }}', 'instance-state-name': 'running'}
| openshift_aws_region                              | us-east-1
| openshift_aws_elb_name                            | {{ openshift_aws_clusterid }}-{{ openshift_aws_node_group_type }}
| openshift_aws_elb_idle_timout                     | 400
| openshift_aws_subnet_name                     | us-east-1c
| openshift_aws_node_group_config_tags              | {{ openshift_aws_clusterid | openshift_aws_build_instance_tags(openshift_aws_kubernetes_cluster_status) }}
| openshift_aws_create_launch_config                | True
| openshift_aws_ami_tags                            | {'bootstrap': 'true', 'clusterid': '{{ openshift_aws_clusterid }}', 'openshift-created': 'true'}
| openshift_aws_ami_name                            | openshift-gi
| openshift_aws_node_group_config_master_volumes    | [{'volume_size': 100, 'delete_on_termination': False, 'device_type': 'gp2', 'device_name': '/dev/sdb'}]
| openshift_aws_vpc_name                            | {{ openshift_aws_clusterid }}
| openshift_aws_elb_listeners                       | {'master': {'internal': [{'instance_port': 80, 'instance_protocol': 'tcp', 'load_balancer_port': 80, 'protocol': 'tcp'}, {'instance_port': 443, 'instance_protocol': 'tcp', 'load_balancer_port': 443, 'protocol': 'tcp'}], 'external': [{'instance_port': 443, 'instance_protocol': 'ssl', 'load_balancer_port': 80, 'protocol': 'tcp'}, {'instance_port': 443, 'instance_protocol': 'ssl', 'load_balancer_port': 443, 'ssl_certificate_id': '{{ openshift_aws_elb_cert_arn }}', 'protocol': 'ssl'}]}}
|


Dependencies
------------


Example Playbook
----------------

```yaml
- include_role:
    name: openshift_aws
    tasks_from: vpc.yml
  vars:
    openshift_aws_clusterid: test
    openshift_aws_region: us-east-1
```

License
-------

Apache License, Version 2.0

Author Information
------------------
