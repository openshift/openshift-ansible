# Installing OSEv3 from dev puddles using ansible

* [Requirements](#requirements)
* [Caveats](#caveats)
* [Known Issues](#known-issues)
* [Configuring the host inventory](#configuring-the-host-inventory)
* [Creating the default variables for the hosts and host groups](#creating-the-default-variables-for-the-hosts-and-host-groups)
* [Running the ansible playbooks](#running-the-ansible-playbooks)
* [Post-ansible steps](#post-ansible-steps)

## Requirements
* ansible
  * Tested using ansible-1.8.2-1.fc20.noarch, but should work with version 1.7+
  * Available in Fedora channels
  * Available for EL with EPEL and Optional channel
* One or more RHEL 7.1 VMs
* ssh key based auth for the root user needs to be pre-configured from the host
  running ansible to the remote hosts
* The enterprise2 branch of openshift-online-ansible from
  https://github.com/detiber/openshift-online-ansible/tree/enterprise2
  
  ```sh
  git clone https://github.com/detiber/openshift-ansible.git -b enterprise2
  cd openshift-ansible
  ```

## Caveats
This ansible repo is currently under heavy revision for providing OSE support;
the following items are highly likely to change before the OSE support is
merged into the upstream repo:
  * the current git branch for testing
  * how the inventory file should be configured
  * variables that need to be set
  * bootstrapping steps
  * other configuration steps

## Known Issues
* Host subscriptions are not configurable yet, the hosts need to be
  pre-registered with subscription-manager or have the RHEL base repo
  pre-configured. If using subscription-manager the following commands will
  disable all but the rhel-7-server rhel-7-server-extras and
  rhel-server7-ose-beta repos:
```sh
subscription-manager repos --disable="*"
subscription-manager repos \
--enable="rhel-7-server-rpms" \
--enable="rhel-7-server-extras-rpms" \
--enable="rhel-server-7-ose-beta-rpms"
```
* The openshift-sdn-master service fails to start when no nodes are registered.
  Will need to either pre-populate the first node(s) in /etc/sysconfig/openshift-master
  or apply the openshift-sdn-master role after the openshift-node role has been applied to one or more hosts.
* Configuration of router is not automated yet
* Configuration of docker-registry is not automated yet
* End-to-end testing has not been completed yet using this module
* root user is used for all ansible actions; eventually we will support using
  a non-root user with sudo.

## Configuring the host inventory
[Ansible docs](http://docs.ansible.com/intro_inventory.html)

Example inventory file for configuring one master and two nodes for the test
environment. This can be configured in the default inventory file
(/etc/ansible/hosts), or using a custom file and passing the --inventory
option to ansible-playbook.

/etc/ansible/hosts:
```ini
# This is an example of a bring your own (byo) host inventory

# host group for masters
[masters]
ose3-master.example.com

# host group for nodes
[nodes]
ose3-node[1:2].example.com
```

The hostnames above should resolve both from the hosts themselves and
the host where ansible is running (if different).

## Creating the default variables for the hosts and host groups
[Ansible docs](http://docs.ansible.com/intro_inventory.html#id9)

#### Group vars for all hosts
/etc/ansible/group_vars/all:
```yaml
---
# Assume that we want to use the root as the ssh user for all hosts
ansible_ssh_user: root

# Default debug level for all OpenShift hosts
openshift_debug_level: 4

# Set the OpenShift deployment type for all hosts
openshift_deployment_type: enterprise

# Assume that all hosts are publicly accessible from the default ipv4
# address (the one that is associated with the default gateway for the
# host). This can also be overridden on a per-host or per-group basis
openshift_public_ip: "{{ ansible_default_ipv4.address }}"

# Override the default registry for development
openshift_registry_url: docker-buildvm-rhose.usersys.redhat.com:5000/openshift3_beta/ose-${component}:${version}

# To use the latest OpenShift Enterprise Errata puddle:
#openshift_additional_repos:
#- id: ose-devel
#  name: ose-devel
#  baseurl: http://buildvm-devops.usersys.redhat.com/puddle/build/OpenShiftEnterpriseErrata/3.0/latest/RH7-RHOSE-3.0/$basearch/os
#  enabled: 1
#  gpgcheck: 0
# To use the latest OpenShift Enterprise Whitelist puddle:
openshift_additional_repos:
- id: ose-devel
  name: ose-devel
  baseurl: http://buildvm-devops.usersys.redhat.com/puddle/build/OpenShiftEnterprise/3.0/latest/RH7-RHOSE-3.0/$basearch/os
  enabled: 1
  gpgcheck: 0

# Override the hostname workaround for byo
openshift_hostname_workaround: false
```

#### Group vars for node hosts
/etc/ansible/group_vars/nodes:
```yaml
---
# This variable makes sure that we are managing the openshift-node service
# from the openshift_sdn_node service, since we are assuming sdn config.
openshift_node_manage_service_externally: true
```

## Running the ansible playbooks
From the openshift-ansible checkout run:
```sh
ansible-playbook playbooks/byo/config.yml
```
**Note:** this assumes that the host inventory is /etc/ansible/hosts and the
group_vars are defined in /etc/ansible/group_vars, if using a different
inventory file (and a group_vars directory that is in the same directory as
the directory as the inventory) use the -i option for ansible-playbook.

## Post-ansible steps
#### Create the default router
On the master host:
```sh
systemctl restart openshift-sdn-master
openshift ex router --create=true \
  --credentials=/var/lib/openshift/openshift.local.certificates/openshift-client/.kubeconfig \
  --images='docker-buildvm-rhose.usersys.redhat.com:5000/openshift3_beta/ose-${component}:${version}'
```

#### Create the default docker-registry
On the master host:
```sh
openshift ex registry --create=true \
  --credentials=/var/lib/openshift/openshift.local.certificates/openshift-client/.kubeconfig \
  --images='docker-buildvm-rhose.usersys.redhat.com:5000/openshift3_beta/ose-${component}:${version}' \
  --mount-host=/var/lib/openshift/docker-registry
```
