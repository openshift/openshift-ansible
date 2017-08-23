openshift_aws_elb
=========

Ansible role to provision and manage AWS ELB's for Openshift.

Requirements
------------

Ansible Modules:

- ec2_elb
- ec2_elb_lb

python package:

python-boto

Role Variables
--------------

- r_openshift_aws_elb_instances: instances to put in ELB
- r_openshift_aws_elb_elb_name: name of elb
- r_openshift_aws_elb_security_group_names: list of SGs (by name) that the ELB will belong to
- r_openshift_aws_elb_region: AWS Region
- r_openshift_aws_elb_health_check: definition of the ELB health check. See ansible docs for ec2_elb
```yaml
  ping_protocol: tcp
  ping_port: 443
  response_timeout: 5
  interval: 30
  unhealthy_threshold: 2
  healthy_threshold: 2
```
- r_openshift_aws_elb_listeners: definition of the ELB listeners. See ansible docs for ec2_elb
```yaml
- protocol: tcp
  load_balancer_port: 80
  instance_protocol: ssl
  instance_port: 443
- protocol: ssl
  load_balancer_port: 443
  instance_protocol: ssl
  instance_port: 443
  # ssl certificate required for https or ssl
  ssl_certificate_id: "{{ r_openshift_aws_elb_cert_arn }}"
```

Dependencies
------------


Example Playbook
----------------
```yaml
- include_role:
    name: openshift_aws_elb
  vars:
    r_openshift_aws_elb_instances: aws_instances_to_put_in_elb
    r_openshift_aws_elb_elb_name: elb_name
    r_openshift_aws_elb_security_groups: security_group_names
    r_openshift_aws_elb_region: aws_region
    r_openshift_aws_elb_health_check: "{{ elb_health_check_definition }}"
    r_openshift_aws_elb_listeners: "{{ elb_listeners_definition }}"
```


License
-------

Apache 2.0

Author Information
------------------

Openshift
