# RHV Playbooks
## Provisioning
This subdirectory contains the Ansible playbooks used to deploy 
an OpenShift Container Platform environment on Red Hat Virtualization

### Where do I start?
Choose a host from which Ansible plays will be executed. This host must have
the ability to access the web interface of the RHV cluster engine and the
network on which the OpenShift nodes will be installed. We will refer to
this host as the *bastion*.

#### oVirt Ansible Roles
The oVirt project maintains Ansible roles for maanaging an oVirt or RHV cluster.
These should be installed on the *bastion* host according to the instructions
at the [oVirt Ansible Roles page](https://github.com/ovirt/ovirt-ansible/).

#### DNS Server
An external DNS server is required to provide name resolution to nodes and
applications. See the
[OpenShift Installation Documentation](https://docs.openshift.com/container-platform/latest/install_config/install/prerequisites.html#prereq-dns)
for details.

One of the playbooks in this subdirectory is capable of using nsupdate to update supported DNS servers automatically, given a servername and copy of the `rndc.key` for the server.

### Let's Provision!
#### High-level overview
After populating inventory and variables files with the proper values,
(see [The OpenShift Advanced Installation Documentation](https://docs.openshift.com/container-platform/latest/install_config/install/advanced_install.html)
) a series of Ansible playbooks from this subdirectory will provision a set of
nodes on the RHV (or oVirt) cluster, prepare them for OpenShift installation,
and deploy an OpenShift cluster on them. If supplied with an *nsupdate* server
and *rndc* key, the entire installation may be performed unattended.

#### Step 1 Inventory
#### Step 2 RHV Provisioning Variables
#### Step 3 Provision Virtual Machines in RHV
#### Step 4 Register (for RHEL) and Subscribe Virtual Machines
#### Step 5 Install Prerequisite Services
#### Step 6 Deploy OpenShift
### Ready To Work!
### Still to come
## Uninstall / Deprovisioning
In case of a failed installation due to a missing variable, it is occasionally necessary to start from a fresh set of virtual machines. Uninstalling the virtual machines and reprovisioning them may be perfomed by running the [`openshift-cluster/unregister-vms.yaml`](openshift-cluster/unregister-vms.yaml) playbook (to recover RHSM entitlements) followed by the [`openshift-cluster/ovirt-vm-uninstall.yaml`](openshift-cluster/ovirt-vm-uninstall.yaml) playbook.
