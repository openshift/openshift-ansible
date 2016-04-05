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

NOTE: This variable is prompted for at the start of the playbook run. This is for security purposes so the password is not left in the command history. If specified on the command-line or set in a variable file it will be ignored and the value captured from the prompt will overwrite it instead.

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

## Calling This Role
Calling this role requires adding a **vars_prompt**, **pre_tasks**, and **roles** section of a play

### vars_prompt
Unfortunately **vars_prompt** can only be used at the play level before role tasks are executed, so this is the only place it can go. See http://stackoverflow.com/questions/25466675/ansible-to-conditionally-prompt-for-a-variable

Add a prompt to capture **rhsm_password**

```
- hosts: localhost
  vars_prompt:
  # Unfortunately vars_prompt can only be used at the play level before role tasks, so this is the only place it can go. See http://stackoverflow.com/questions/25466675/ansible-to-conditionally-prompt-for-a-variable
    - name: "rhsm_password"
      prompt: "Subscription Manager password (enter blank if using rhsm_activationkey or to disable registration)"
      confirm: yes
      private: yes
```

### pre-tasks

A number of variable checks are performed before any tasks to ensure the proper parameters are set. To include these checks call the pre_task yaml before any roles:

```
  pre_tasks:
  - include: roles/subscription-manager/pre_tasks/pre_tasks.yml 
```

### roles

The bulk of the work is performed in the main.yml for this role. The pre-task play will set a variable which can be checked to contitionally include this role as such:

```
  roles:
    - { role: subscription-manager, when: hostvars.localhost.rhsm_register, tags: 'subscription-manager' }
```

## Running the Playbook
 
To register to RHSM Hosted with username and password:

```
ansible-playbook -i inventory/ose-provision ose-provision.yml -e "rhsm_username=vvaldez"
```

To register to a Satellite server with an activation key:

```
ansible-playbook -i inventory/ose-provision ose-provision.yml -e "rhsm_satellite=satellite.example.com rhsm_org=example_org rhsm_activationkey=rhel-7-ose-3-1"
```

To ignore any Subscription Manager activities, simply do not set any parameters. When prompted for the password, hit **Enter** to set a blank password.
