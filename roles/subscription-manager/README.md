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

NOTE: If this variable is specified on the command-line or set in a variable file it may leave your password exposed. For this reason you may perfer to use an Activation Key if using Satellite. For RHSM Hosted, your password must be specified. There are two ways to provide the password to the Ansible playbook without exposing it to prying eyes.

1. The first method is to use a **vars_prompt** to collect the password up front one time for the playbook. Ansible will not display the password if the prompt is configured as **private** and the task will not display the password on the CLI. This is the a good method as it supports automating the task to every host with only one password entry. To enable **vars_prompt** add the following to the very top of your playbook after the **hosts** declaration and before any **pre_tasks** section:

    ```
    - hosts: localhost
      # Add the following lines after a -hosts: declaration and before pre_tasks:
      # Start of vars_prompt code block
      vars_prompt:
        - name: "rhsm_password"
          prompt: "Subscription Manager password"
          confirm: yes
          private: yes
      # End of vars_prompt code block
      pre_tasks:
    ```

2. A second method is to use an encrypted file via **ansible-vault**. This does does not require modifying any code as the previous method, but does require more work to create and encrypt the file. To accomplish this, first create a file containing at least the **rhsm_password** variable (it is also possible to specify additional variables to encrypt them all as well):
  1. Create a file to contain the variable such as **secrets.yml**:

    ```
    ---
    rhsm_password: "my_secret_password"
    # other variables can optionally be placed here as well
    ```

  2. Encrypt the file with **ansible-vault**:

    ```
    $ ansible-vault encrypt secrets.yml
    Vault password: 
    Confirm Vault password: 
    Encryption successful
    ```

  3. When executing **ansible-playbook** specify **--ask-vault-pass** to be prompted for the decryption password, and also specify the location of the **secrets.yml** as such:

    ```
    $ ansible-playbook --ask-vault-pass --extra-vars=@secrets.yml --extra-vars="rhsm_username=myusername" <other playbook options>
    ```

  NOTE: Optionally the file containing the encrypted variables can be decrypted with **ansible-vault** and the **--ask-vault-pass** option omitted to prevent any password prompting (for automated runs) and the file can be encrypted after the run. This can be used if an external system such as Jenkins would handle the decryption/encryption outside of Ansible.

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
Calling this role is done at both **pre_tasks** and **roles** sections of a playbook and optionally a **vars_prompt**.

### vars_prompt
Unfortunately **vars_prompt** can only be used at the play level before role tasks are executed, so this is the only place it can go. It also cannot be shown conditionally. For this reason it is not included in this role by default. A better method may be using a file containing the password variable encrypted with **ansible-vault**. See the **rhsm_password** section for more details.

To Add a prompt to capture **rhsm_password**:

```
- hosts: localhost
  # Add the following lines after a -hosts: declaration and before pre_tasks:
  # Start of vars_prompt code block
  vars_prompt:
    - name: "rhsm_password"
      prompt: "Subscription Manager password"
      confirm: yes
      private: yes
  # End of vars_prompt code block
  pre_tasks:
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

## Running Playbooks with this Role
 
- To register to RHSM Hosted or Satellite with a username and plain text password (NOTE: This may retain your password in your CLI history):

    ```
    $ ansible-playbook --extra-vars="rhsm_username=vvaldez rhsm_password=my_secret_password <other playbook otions>"
    ```

- To register to RHSM Hosted or Satellite with username and an encrypted file containing the password:

    ```
    $ ansible-playbook --ask-vault-pass --extra-vars=@secrets.yml --extra-vars="rhsm_username=myusername" <other playbook options>

    ```

- To register to a Satellite server with an activation key:

    ```
    $ ansible-playbook --extra-vars="rhsm_satellite=satellite.example.com rhsm_org=example_org rhsm_activationkey=rhel-7-ose-3-1 <other playbook options>"

    ```
- To ignore any Subscription Manager activities, simply do not set any parameters.
