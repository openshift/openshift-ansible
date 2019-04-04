# Hooks

OpenShift Ansible allows for operators to execute custom tasks during
specific operations through a system called hooks. Hooks allow operators to
provide files defining tasks to execute before and/or after specific areas
during upgrades. This can be very helpful to validate
or modify custom infrastructure when upgrading RHEL nodes in OpenShift.

It is important to remember that when a hook fails the operation fails. This
means a good hook can run multiple times and provide the same results. A great
hook is idempotent.

## Using Hooks

Hooks are defined in the ``hosts`` inventory file under the ``all:vars``
section.

Each hook should point to a yaml file which defines Ansible tasks. This file
will be used as an include meaning that the file can not be a playbook but
a set of tasks. Best practice suggests using absolute paths to the hook file to avoid any ambiguity.

### Example inventory variables
```ini
[all:vars]
# <snip>
openshift_node_pre_cordon_hook=/usr/share/custom/pre_cordon.yml
openshift_node_pre_upgrade_hook=/usr/share/custom/pre_upgrade.yml
openshift_node_pre_uncordon_hook=/usr/share/custom/pre_uncordon.yml
openshift_node_post_upgrade_hook=/usr/share/custom/post_upgrade.yml
# <snip>
```

Hook files must be a yaml formatted file that defines a set of Ansible tasks.
The file may **not** be a playbook.

### Example hook task file
```yaml

---
# Trivial example forcing an operator to ack the start of an upgrade
# file=/usr/share/custom/pre_cordon.yml

- name: note the start of a node upgrade
  debug:
    msg: "Node upgrade of {{ inventory_hostname }} is about to start"

- name: require an operator agree to start an upgrade
  pause:
    prompt: "Hit enter to start the node upgrade"
```

## Available Upgrade Hooks

### openshift_node_pre_cordon_hook
- Runs **before** each node is cordoned.
- This hook runs against **each node** in serial.
- If a task needs to run against a different host, said task will need to use [``delegate_to`` or ``local_action``](http://docs.ansible.com/ansible/playbooks_delegation.html#delegation).

### openshift_node_pre_upgrade_hook
- Runs **after** each node is cordoned but **before** it is upgraded.
- This hook runs against **each node** in serial.
- If a task needs to run against a different host, said task will need to use [``delegate_to`` or ``local_action``](http://docs.ansible.com/ansible/playbooks_delegation.html#delegation).

### openshift_node_pre_uncordon_hook
- Runs **after** each node is upgraded but **before** it is uncordoned.
- This hook runs against **each node** in serial.
- If a task needs to run against a different host, said task will need to use [``delegate_to`` or ``local_action``](http://docs.ansible.com/ansible/playbooks_delegation.html#delegation).

### openshift_node_post_upgrade_hook
- Runs **after** each node is uncordoned; it's the last node upgrade action.
- This hook runs against **each node** in serial.
- If a task needs to run against a different host, said task will need to use [``delegate_to`` or ``local_action``](http://docs.ansible.com/ansible/playbooks_delegation.html#delegation).
