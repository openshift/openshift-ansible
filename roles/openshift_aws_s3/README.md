openshift_aws_s3
=========

Ansible role to create an s3 bucket

Requirements
------------

Ansible Modules:


Role Variables
--------------

- r_openshift_aws_s3_clusterid: myclusterid
- r_openshift_aws_s3_region: us-east-1
- r_openshift_aws_s3_mode:  create|delete

Dependencies
------------


Example Playbook
----------------
```yaml
- name: create an s3 bucket
  include_role:
    name: openshift_aws_s3
  vars:
    r_openshift_aws_s3_clusterid: mycluster
    r_openshift_aws_s3_region: us-east-1
    r_openshift_aws_s3_mode: create
```

License
-------

Apache 2.0

Author Information
------------------

Openshift
