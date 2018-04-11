# Hooks

The ansible installer allows for operators to execute custom tasks during
specific operations through a system called hooks. Hooks allow operators to
provide files defining tasks to execute before and/or after specific areas
during installations and upgrades. This can be very helpful to validate
or modify custom infrastructure when installing/upgrading OpenShift.

It is important to remember that when a hook fails the operation fails. This
means a good hook can run multiple times and provide the same results. A great
hook is idempotent.

**Note**: There is currently not a standard interface for hooks. In the future
a standard interface will be defined and any hooks that existed previously will
need to be updated to meet the new standard.

## Using Hooks

Hooks are defined in the ``hosts`` inventory file under the ``OSEv3:vars``
section.

Each hook should point to a yaml file which defines Ansible tasks. This file
will be used as an include meaning that the file can not be a playbook but
a set of tasks. Best practice suggests using absolute paths to the hook file to avoid any ambiguity.

### Example
```ini
[OSEv3:vars]
# <snip>
openshift_master_upgrade_pre_hook=/usr/share/custom/pre_master.yml
openshift_master_upgrade_hook=/usr/share/custom/master.yml
openshift_master_upgrade_post_hook=/usr/share/custom/post_master.yml

openshift_node_upgrade_pre_hook=/usr/share/custom/pre_node.yml
openshift_node_upgrade_hook=/usr/share/custom/node.yml
openshift_node_upgrade_post_hook=/usr/share/custom/post_node.yml
# <snip>
```

Hook files must be a yaml formatted file that defines a set of Ansible tasks.
The file may **not** be a playbook.

### Example
```yaml
---
# Trivial example forcing an operator to ack the start of an upgrade
# file=/usr/share/custom/pre_master.yml

- name: note the start of a master upgrade
  debug:
      msg: "Master upgrade of {{ inventory_hostname }} is about to start"

- name: require an operator agree to start an upgrade
  pause:
      prompt: "Hit enter to start the master upgrade"
```

## Upgrade Hooks

### openshift_master_upgrade_pre_hook
- Runs **before** each master is upgraded.
- This hook runs against **each master** in serial.
- If a task needs to run against a different host, said task will need to use [``delegate_to`` or ``local_action``](http://docs.ansible.com/ansible/playbooks_delegation.html#delegation).

### openshift_master_upgrade_hook
- Runs **after** each master is upgraded but **before** it's service/system restart.
- This hook runs against **each master** in serial.
- If a task needs to run against a different host, said task will need to use [``delegate_to`` or ``local_action``](http://docs.ansible.com/ansible/playbooks_delegation.html#delegation).


### openshift_master_upgrade_post_hook
- Runs **after** each master is upgraded and has had it's service/system restart.
- This hook runs against **each master** in serial.
- If a task needs to run against a different host, said task will need to use [``delegate_to`` or ``local_action``](http://docs.ansible.com/ansible/playbooks_delegation.html#delegation).

### openshift_node_upgrade_pre_hook
- Runs **before** each node is upgraded.
- This hook runs against **each node** in serial.
- If a task needs to run against a different host, said task will need to use [``delegate_to`` or ``local_action``](http://docs.ansible.com/ansible/playbooks_delegation.html#delegation).

### openshift_node_upgrade_hook
- Runs **after** each node is upgraded but **before** it's marked schedulable again..
- This hook runs against **each node** in serial.
- If a task needs to run against a different host, said task will need to use [``delegate_to`` or ``local_action``](http://docs.ansible.com/ansible/playbooks_delegation.html#delegation).

### openshift_node_upgrade_post_hook
- Runs **after** each node is upgraded; it's the last node upgrade action.
- This hook runs against **each node** in serial.
- If a task needs to run against a different host, said task will need to use [``delegate_to`` or ``local_action``](http://docs.ansible.com/ansible/playbooks_delegation.html#delegation).

