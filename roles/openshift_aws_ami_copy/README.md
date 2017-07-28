openshift_aws_ami_perms
=========

Ansible role for copying an AMI

Requirements
------------

Ansible Modules:


Role Variables
--------------

- openshift_aws_ami_copy_src_ami: source AMI id to copy from
- openshift_aws_ami_copy_region: region where the AMI is found
- openshift_aws_ami_copy_name: name to assign to new AMI
- openshift_aws_ami_copy_kms_arn: AWS IAM KMS arn of the key to use for encryption
- openshift_aws_ami_copy_tags: dict with desired tags
- openshift_aws_ami_copy_wait: wait for the ami copy to achieve available status.  This fails due to boto waiters.

Dependencies
------------


Example Playbook
----------------
```yaml
    - name: copy the ami for encrypted disks
      include_role:
        name: openshift_aws_ami_copy
      vars:
        r_openshift_aws_ami_copy_region: us-east-1
        r_openshift_aws_ami_copy_name: myami
        r_openshift_aws_ami_copy_src_ami: ami-1234
        r_openshift_aws_ami_copy_kms_arn: arn:xxxx
        r_openshift_aws_ami_copy_tags: {}
        r_openshift_aws_ami_copy_encrypt: False

```

License
-------

Apache 2.0

Author Information
------------------

Openshift
