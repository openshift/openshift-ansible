:warning: **WARNING** :warning: This feature is community supported and has not been tested by Red Hat. Visit [docs.openshift.com](https://docs.openshift.com) for [OpenShift Enterprise](https://docs.openshift.com/enterprise/latest/install_config/install/index.html) or [OpenShift Origin](https://docs.openshift.org/latest/install_config/install/index.html) supported installation docs.

OPENSTACK Setup instructions
============================

Requirements
------------

The OpenStack instance must have Neutron and Heat enabled.

Install Dependencies
--------------------

1. The OpenStack python clients for Nova, Neutron and Heat are required:

* `python-novaclient`
* `python-neutronclient`
* `python-heatclient`

On Fedora:
```
  dnf install -y ansible python-novaclient python-neutronclient python-heatclient
```

On RHEL / CentOS:
```
  yum install -y ansible python-novaclient python-neutronclient python-heatclient
  sudo pip install shade
```

Configuration
-------------

The following options can be passed via the `-o` flag of the `create` command:

* `infra_heat_stack` (default to `playbooks/openstack/openshift-cluster/files/heat_stack.yaml`): filename of the HEAT template to use to create the cluster infrastructure

The following options are used only by `heat_stack.yaml`. They are so used only if the `infra_heat_stack` option is left with its default value.

* `image_name`: Name of the image to use to spawn VMs
* `public_key` (default to `~/.ssh/id_rsa.pub`): filename of the ssh public key
* `etcd_flavor` (default to `m1.small`): The ID or name of the flavor for the etcd nodes
* `master_flavor` (default to `m1.small`): The ID or name of the flavor for the master
* `node_flavor` (default to `m1.medium`): The ID or name of the flavor for the compute nodes
* `infra_flavor` (default to `m1.small`): The ID or name of the flavor for the infrastructure nodes
* `network_prefix` (default to `openshift-ansible-<cluster_id>`): prefix prepended to all network objects (net, subnet, router, security groups)
* `dns` (default to `8.8.8.8,8.8.4.4`): comma separated list of DNS to use
* `net_cidr` (default to `192.168.<rand()>.0/24`): CIDR of the network created by `heat_stack.yaml`
* `external_net` (default to `external`): Name of the external network to connect to
* `floating_ip_pool` (default to `external`): comma separated list of floating IP pools
* `ssh_from` (default to `0.0.0.0/0`): IPs authorized to connect to the VMs via ssh
* `node_port_from` (default to `0.0.0.0/0`): IPs authorized to connect to the services exposed via nodePort
* `heat_timeout` (default to `3`): Timeout (in minutes) passed to heat for create or update stack.


Creating a cluster
------------------

1. To create a cluster with one master and two nodes

```
  bin/cluster create openstack <cluster-id>
```

2. To create a cluster with one master and three nodes, a custom VM image and custom DNS:

```
  bin/cluster create -n 3 -o image_name=rhel-7.1-openshift-2015.05.21 -o dns=172.16.50.210,172.16.50.250 openstack lenaic
```

Updating a cluster
------------------

1. To update the cluster

```
  bin/cluster update openstack <cluster-id>
```

Terminating a cluster
---------------------

1. To terminate the cluster

```
  bin/cluster terminate openstack <cluster-id>
```
