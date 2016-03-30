# Red Hat Subscription Manager Ansible Role

## Parameters

This role depends on user specified variables. These can be set in the inventory file, group_vars or passed to the playbook from the CLI. No values are set by default which disables this role. The variables are:

### rhsm_satellite

Subscription Manager server hostname. If using a Satellite server set the FQDN here. If using RHSM Hosted this value must be left blank, none or false.

Default: none

### rhsm_username

Subscription Manager username. Required for RHSM Hosted. Can be optionally used for Satellite, but it may be better to use **rhsm_activationkey** for this.

Default: none

### rhsm_password

Subscription Manager password. Required for RHSM Hosted. Can be optionally used for Satellite, but it may be better to use **rhsm_activationkey** for this.

Default: none

### rhsm_org

Optional Subscription Manager Satellite Organization. Required for Satellite, ignored if using RHSM Hosted.

Default: none

### rhsm_activationkey

Optional Subscription Manager Satellite Activation Key, use this instead of **rhsm_username** and **rhsm_password** if using Satellite to provide repositories and authentication in a key instead.

Default: none

### rhsm_pool

Optional Subscription Manager pool, determine this by running **subscription-manager list --available** on a registered system. Valid for RHSM Hosted or Satellite. Specifying **rhsm_activationkey** will ignore this option.

Default: none

### rhsm_repos

Optional list of repositories to enable. If left blank it is expected that the **rhsm_activationkey** will specify repos instead.  If populated, a **subscription-manager repos --disable=\*** will be run and each of the specified repos explicitly enabled. Valid for RHSM Hosted or Satellite

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
    - { role: subscription-manager, when: hostvars.localhost.rhsm_register, tags: 'subscription-manager' }
```

## Running the Playbook
 
To register to RHSM Hosted with username and password:

```
ansible-playbook -i inventory/ose-provision ose-provision.yml -e "rhsm_username=vvaldez rhsm_password=hunter2"
```

To register to a Satellite server with an activation key:

```
ansible-playbook -i inventory/ose-provision ose-provision.yml -e "rhsm_satellite=satellite.example.com rhsm_org=example_org rhsm_activationkey=rhel-7-ose-3-1"
```

To ignore any Subscription Manager activities, simply do not set any parameters.
