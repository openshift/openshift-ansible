# OpenStack Provisioning

This directory contains [Ansible][ansible] playbooks and roles to create
OpenStack resources (servers, networking, volumes, security groups,
etc.). The result is an environment ready for OpenShift installation
via [openshift-ansible].

We provide everything necessary to be able to install OpenShift on
OpenStack (including the DNS and load balancer servers when
necessary). In addition, we work on providing integration with the
OpenStack-native services (storage, lbaas, baremetal as a service,
dns, etc.).


## OpenStack Requirements

Before you start the installation, you need to have an OpenStack
environment to connect to. You can use a public cloud or an OpenStack
within your organisation. It is also possible to
use [Devstack][devstack] or [TripleO][tripleo]. In the case of
TripleO, we will be running on top of the **overcloud**.

The OpenStack release must be Newton (for Red Hat OpenStack this is
version 10) or newer. It must also satisfy these requirements:

* Heat (Orchestration) must be available
* The deployment image (CentOS 7 or RHEL 7) must be loaded
* The deployment flavor must be available to your user
  - `m1.medium` / 4GB RAM + 40GB disk should be enough for testing
  - look at
    the [Minimum Hardware Requirements page][hardware-requirements]
    for production
* The keypair for SSH must be available in openstack
* `keystonerc` file that lets you talk to the openstack services
   * NOTE: only Keystone V2 is currently supported

Optional:
* External Neutron network with a floating IP address pool


## Installation

There are four main parts to the installation:

1. [Preparing Ansible and dependencies](#1-preparing-ansible-and-dependencies)
2. [Configuring the desired OpenStack environment and OpenShift cluster](#2-configuring-the-openstack-environment-and-openshift-cluster)
3. [Creating the OpenStack resources (VMs, networking, etc.)](#3-creating-the-openstack-resources-vms-networking-etc)
4. [Installing OpenShift](#4-installing-openshift)

This guide is going to install [OpenShift Origin][origin]
with [CentOS 7][centos7] images with minimal customisation.

We will create the VMs for running OpenShift, in a new Neutron
network, assign Floating IP addresses and configure DNS.

The OpenShift cluster will have a single Master node that will run
`etcd`, a single Infra node and two App nodes.

You can look at
the [Advanced Configuration page][advanced-configuration] for
additional options.



### 1. Preparing Ansible and dependencies

First, you need to select where to run [Ansible][ansible] from (the
*Ansible host*). This can be the computer you read this guide on or an
OpenStack VM you'll create specifically for this purpose.

We will use
a
[Docker image that has all the dependencies installed][control-host-image] to
make things easier. If you don't want to use Docker, take a look at
the [Ansible host dependencies][ansible-dependencies] and make sure
they're installed.

Your *Ansible host* needs to have the following:

1. Docker
2. `keystonerc` file with your OpenStack credentials
3. SSH private key for logging in to your OpenShift nodes

Assuming your private key is `~/.ssh/id_rsa` and `keystonerc` in your
current directory:

```bash
$ sudo docker run -it -v ~/.ssh:/mnt/.ssh:Z \
     -v $PWD/keystonerc:/root/.config/openstack/keystonerc.sh:Z \
     redhatcop/control-host-openstack bash
```

This will create the container, add your SSH key and source your
`keystonerc`. It should be set up for the installation.

You can verify that everything is in order:


```bash
$ less .ssh/id_rsa
$ ansible --version
$ openstack image list
```


### 2. Configuring the OpenStack Environment and OpenShift Cluster

The configuration is all done in an Ansible inventory directory. We
will clone the [openshift-ansible-contrib][contrib] repository and set
things up for a minimal installation.


```
$ git clone https://github.com/openshift/openshift-ansible-contrib
$ cp -r openshift-ansible-contrib/playbooks/provisioning/openstack/sample-inventory/ inventory
```

If you're testing multiple configurations, you can have multiple
inventories and switch between them.

#### OpenStack Configuration

The OpenStack configuration is in `inventory/group_vars/all.yml`.

Open the file and plug in the image, flavor and network configuration
corresponding to your OpenStack installation.

```bash
$ vi inventory/group_vars/all.yml
```

1. Set the `openstack_ssh_public_key` to your OpenStack keypair name.
   - See `openstack keypair list` to find the keypairs registered with
   OpenShift.
   - This must correspond to your private SSH key in `~/.ssh/id_rsa`
2. Set the `openstack_external_network_name` to the floating IP
   network of your openstack.
   - See `openstack network list` for the list of networks.
   - It's often called `public`, `external` or `ext-net`.
3. Set the `openstack_default_image_name` to the image you want your
   OpenShift VMs to run.
   - See `openstack image list` for the list of available images.
4. Set the `openstack_default_flavor` to the flavor you want your
   OpenShift VMs to use.
   - See `openstack flavor list` for the list of available flavors.

**NOTE**: In most OpenStack environments, you will also need to
configure the forwarders for the DNS server we create. This depends on
your environment.

Launch a VM in your OpenStack and look at its `/etc/resolv.conf` and
put the IP addresses into `public_dns_nameservers` in
`inventory/group_vars/all.yml`.


#### OpenShift configuration

The OpenShift configuration is in `inventory/group_vars/OSEv3.yml`.

The default options will mostly work, but unless you used the large
flavors for a production-ready environment, openshift-ansible's
hardware check will fail.

Let's disable those checks by putting this in
`inventory/group_vars/OSEv3.yml`:

```yaml
openshift_disable_check: disk_availability,memory_availability
```

**NOTE**: The default authentication method will allow **any username
and password** in! If you're running this in a public place, you need
to set up access control.

Feel free to look at
the [Sample OpenShift Inventory][sample-openshift-inventory] and
the [advanced configuration][advanced-configuration].


### 3. Creating the OpenStack resources (VMs, networking, etc.)

We will install the DNS server roles using ansible galaxy and then run
the openstack provisioning playbook. The `ansible.cfg` file we provide
has useful defaults -- copy it to the directory you're going to run
Ansible from.

```bash
$ ansible-galaxy install -r openshift-ansible-contrib/playbooks/provisioning/openstack/galaxy-requirements.yaml -p openshift-ansible-contrib/roles
$ cp openshift-ansible-contrib/playbooks/provisioning/openstack/ansible.cfg ansible.cfg
```
(you will only need to do this once)

Then run the provisioning playbook -- this will create the OpenStack
resources:

```bash
$ ansible-playbook -i inventory openshift-ansible-contrib/playbooks/provisioning/openstack/provision.yaml
```

If you're using multiple inventories, make sure you pass the path to
the right one to `-i`.


### 4. Installing OpenShift

We will use the `openshift-ansible` project to install openshift on
top of the OpenStack nodes we have prepared:

```bash
$ git clone https://github.com/openshift/openshift-ansible
$ ansible-playbook -i inventory openshift-ansible/playbooks/byo/config.yml
```


### Next Steps

And that's it! You should have a small but functional OpenShift
cluster now.

Take a look at [how to access the cluster][accessing-openshift]
and [how to remove it][uninstall-openshift] as well as the more
advanced configuration:

* [Accessing the OpenShift cluster][accessing-openshift]
* [Removing the OpenShift cluster][uninstall-openshift]
* Set Up Authentication (TODO)
* [Multiple Masters with a load balancer][loadbalancer]
* [External Dns][external-dns]
* Multiple Clusters (TODO)
* [Cinder Registry][cinder-registry]
* [Bastion Node][bastion]


[ansible]: https://www.ansible.com/
[openshift-ansible]: https://github.com/openshift/openshift-ansible
[devstack]: https://docs.openstack.org/devstack/
[tripleo]: http://tripleo.org/
[ansible-dependencies]: ./advanced-configuration.md#dependencies-for-localhost-ansible-controladmin-node
[contrib]: https://github.com/openshift/openshift-ansible-contrib
[control-host-image]: https://hub.docker.com/r/redhatcop/control-host-openstack/
[hardware-requirements]: https://docs.openshift.org/latest/install_config/install/prerequisites.html#hardware
[origin]: https://www.openshift.org/
[centos7]: https://www.centos.org/
[sample-openshift-inventory]: https://github.com/openshift/openshift-ansible/blob/master/inventory/byo/hosts.example
[advanced-configuration]: ./advanced-configuration.md
[accessing-openshift]: ./advanced-configuration.md#accessing-the-openshift-cluster
[uninstall-openshift]: ./advanced-configuration.md#removing-the-openshift-cluster
[loadbalancer]: ./advanced-configuration.md#multi-master-configuration
[external-dns]: ./advanced-configuration.md#dns-configuration-variables
[cinder-registry]: ./advanced-configuration.md#creating-and-using-a-cinder-volume-for-the-openshift-registry
[bastion]: ./advanced-configuration.md#configure-static-inventory-and-access-via-a-bastion-node



## License

Like the rest of the openshift-ansible-contrib repository, the code
here is licensed under Apache 2.
