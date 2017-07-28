openshift_aws_vpc
=========

Ansible role to create a default AWS VPC

Requirements
------------

Ansible Modules:


Role Variables
--------------

- r_openshift_aws_vpc_clusterid: "{{ clusterid }}"
- r_openshift_aws_vpc_cidr: 172.31.48.0/20
- r_openshift_aws_vpc_subnets: "{{ subnets }}"
```yaml
    subnets:
      us-east-1:  # These are us-east-1 region defaults. Ensure this matches your region
      - cidr: 172.31.48.0/20
        az: "us-east-1c"
      - cidr: 172.31.32.0/20
        az: "us-east-1e"
      - cidr: 172.31.16.0/20
        az: "us-east-1a"
```
- r_openshift_aws_vpc_region: "{{ region }}"
- r_openshift_aws_vpc_tags: dict of tags to apply to vpc
- r_openshift_aws_vpc_name: "{{ vpc_name | default(clusterid) }}"

Dependencies
------------


Example Playbook
----------------

```yaml
  - name: create default vpc
    include_role:
      name: openshift_aws_vpc
    vars:
      r_openshift_aws_vpc_clusterid: mycluster
      r_openshift_aws_vpc_cidr: 172.31.48.0/20
      r_openshift_aws_vpc_subnets: "{{ subnets }}"
      r_openshift_aws_vpc_region: us-east-1
      r_openshift_aws_vpc_tags: {}
      r_openshift_aws_vpc_name: mycluster

```


License
-------

Apache 2.0

Author Information
------------------

Openshift
