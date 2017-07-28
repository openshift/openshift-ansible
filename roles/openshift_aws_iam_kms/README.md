openshift_aws_iam_kms
=========

Ansible role to create AWS IAM KMS keys for encryption

Requirements
------------

Ansible Modules:

oo_iam_kms

Role Variables
--------------

- r_openshift_aws_iam_kms_region: AWS region to create KMS key
- r_openshift_aws_iam_kms_alias: Alias name to assign to created KMS key

Dependencies
------------

lib_utils

Example Playbook
----------------
```yaml
- include_role:
    name: openshift_aws_iam_kms
  vars:
    r_openshift_aws_iam_kms_region: 'us-east-1'
    r_openshift_aws_iam_kms_alias: 'alias/clusterABC_kms'
```


License
-------

Apache 2.0

Author Information
------------------

Openshift
