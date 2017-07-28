openshift_aws_sg
=========

Ansible role to create an aws security groups

Requirements
------------

Ansible Modules:


Role Variables
--------------

- r_openshift_aws_sg_clusterid: myclusterid
- r_openshift_aws_sg_region: us-east-1
- r_openshift_aws_sg_type: master|infra|compute
```yaml
# defaults/main.yml
  default:
    name: "{{ r_openshift_aws_sg_clusterid }}"
    desc: "{{ r_openshift_aws_sg_clusterid }} default"
    rules:
    - proto: tcp
      from_port: 22
      to_port: 22
      cidr_ip: 0.0.0.0/0
    - proto: all
      from_port: all
      to_port: all
      group_name: "{{ r_openshift_aws_sg_clusterid }}"
```


Dependencies
------------


Example Playbook
----------------
```yaml
- name: create security groups for master
  include_role:
    name: openshift_aws_sg
  vars:
    r_openshift_aws_sg_clusterid: mycluster
    r_openshift_aws_sg_region: us-east-1
    r_openshift_aws_sg_type: master
```

License
-------

Apache 2.0

Author Information
------------------

Openshift
