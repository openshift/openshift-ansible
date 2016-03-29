# Red Hat Subscription Manager Ansible Role

## Parameters

This role depends on user specified variables. These can be set in the inventory file, group_vars or passed to the playbook from the CLI. The variables are:

### rhsm_method

Subscription Manager method to use for registration. Valid values are:

* **satellite** - Use a Satellite server. Additional variables required include **rhsm_server**, **rhsm_org** and either (**rhsm_username** and **rhsm_password**) or **rhsm_activationkey**
* **hosted** - Use Red Hat's CDN. Additional variables required are **rhsm_server** (defaults to RHSM CDN) and **rhsm_username** and **rhsm_password**
* none/false/blank will disable any subscription manager activities (this is the default if no parameters are set)

Default: none

### rhsm_server

Subscription Manager server hostname. If using a Satellite server set the FQDN here. If using RHSM Hosted this value is ignored.

Default: none

### rhsm_username

Subscription Manager username. Required for RHSM Hosted. Can be optionally used for Satellite, but it may be better to use **rhsm_activationkey** for this.

Default: none

### rhsm_password

Subscription Manager password. Required for RHSM Hosted. Can be optionally used for Satellite, but it may be better to use **rhsm_activationkey** for this.

Default: none

### rhsm_org

Optional Satellite Subscription Manager Organization. Required for Satellite, ignored if using RHSM Hosted.

Default: none

### rhsm_activationkey

Optional Satellite Subscription Manager Activation Key, use this instead of **rhsm_username** and **rhsm_password** if using Satellite to provide repositories and authentication in a key instead.

Default: none

### rhsm_pool

Optional Subscription Manager pool, determine this by running **subscription-manager list --available** on a registered system. Valid for RHSM Hosted or Satellite. Specifying **rhsm_activationkey** will ignore this option.

Default: none

### rhsm_repos

Optional Repositories to enable, this can also be specified in the **rhsm_activationkey**. Valid for RHSM Hosted or Satellite. Specifying **rhsm_activationkey** will ignore this option.

NOTE: If specifying this value in an inventory file as opposed to group_vars, be sure to define it as a proper list as such:

rhsm_repos='["rhel-7-server-rpms", "rhel-7-server-ose-3.1-rpms", "rhel-7-server-extras-rpms"]'

Default: none

## Pre-tasks

A number of variable checks are performed before any tasks to ensure the proper parameters are set. To include these checks call the pre_task yaml before any roles:

```
  pre_tasks:
  - include: roles/subscription-manager/pre_tasks/pre_tasks.yml 
```

## Tasks

The bulk of the work is performed in the main.yml for this role. The pre-task play will set a variable which can be checked to contitionally include this role as such:

```
  roles:
    - { role: subscription-manager, when: not hostvars.localhost.rhsm_skip, tags: 'subscription-manager' }
```

## Running the Playbook
 
To register to RHSM Hosted with username and password:

```
ansible-playbook -i inventory/ose-provision ose-provision.yml -e "rhsm_method='hosted' rhsm_username=vvaldez rhsm_password='hunter2' openstack_key_name='vvaldez'"
```

To register to a Satellite server with an activation key:

```
ansible-playbook -i inventory/ose-provision ose-provision.yml -e "rhsm_server='10.12.32.1' rhsm_org='cloud_practice' rhsm_activationkey='rhel-7-ose-3-1' openstack_key_name='vvaldez' rhsm_method='satellite'"
```

To ignore any Subscription Manager activities, simple do not set any parameters or explicitly set **rhsm_method** to false.
