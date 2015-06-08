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

On RHEL / CentOS / Fedora:
```
  yum install -y ansible python-novaclient python-neutronclient python-heatclient
```

Configuration
-------------

The following options can be passed via the `-o` flag of the `create` command:

* `image_name`: Name of the image to use to spawn VMs
* `keypair` (default to `${LOGNAME}_key`): Name of the ssh key
* `public_key` (default to `~/.ssh/id_rsa.pub`): filename of the ssh public key
* `master_flavor_ram` (default to `2048`): VM flavor for the master (by amount of RAM)
* `master_flavor_id`: VM flavor for the master (by ID)
* `master_flavor_include`: VM flavor for the master (by name)
* `node_flavor_ram` (default to `4096`): VM flavor for the nodes (by amount of RAM)
* `node_flavor_id`: VM flavor for the nodes (by ID)
* `node_flavor_include`: VM flavor for the nodes (by name)
* `infra_heat_stack` (default to `playbooks/openstack/openshift-cluster/files/heat_stack.yml`): filename of the HEAT template to use to create the cluster infrastructure

The following options are used only by `heat_stack.yml`. They are so used only if the `infra_heat_stack` option is left with its default value.

* `network_prefix` (default to `openshift-ansible-<cluster_id>`): prefix prepended to all network objects (net, subnet, router, security groups)
* `dns` (default to `8.8.8.8,8.8.4.4`): comma separated list of DNS to use
* `net_cidr` (default to `192.168.<rand()>.0/24`): CIDR of the network created by `heat_stack.yml`
* `external_net` (default to `external`): Name of the external network to connect to
* `floating_ip_pools` (default to `external`): comma separated list of floating IP pools
* `ssh_from` (default to `0.0.0.0/0`): IPs authorized to connect to the VMs via ssh


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
