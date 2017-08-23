openshift_aws_ssh_keys
=========

Ansible role for sshind SSH keys

Requirements
------------

Ansible Modules:


Role Variables
--------------

- r_openshift_aws_ssh_keys_users: list of dicts of users
- r_openshift_aws_ssh_keys_region: ec2_region to install the keys

Dependencies
------------


Example Playbook
----------------
```yaml
users:
- username: user1
  pub_key: <user1 ssh public key>
- username: user2
  pub_key: <user2 ssh public key>

region: us-east-1

- include_role:
    name: openshift_aws_ssh_keys
  vars:
    r_openshift_aws_ssh_keys_users: "{{ users }}"
    r_openshift_aws_ssh_keys_region: "{{ region }}"
```


License
-------

Apache 2.0

Author Information
------------------

Openshift
