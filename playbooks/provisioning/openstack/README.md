# OpenStack Provisioning

This repository contains playbooks and Heat templates to provision
OpenStack resources (servers, networking, volumes, security groups,
etc.). The result is an environment ready for openshift-ansible.

## Dependencies for localhost (ansible control/admin node)

* [Ansible 2.3](https://pypi.python.org/pypi/ansible)
* [Ansible-galaxy](https://pypi.python.org/pypi/ansible-galaxy-local-deps)
* [jinja2](http://jinja.pocoo.org/docs/2.9/)
* [shade](https://pypi.python.org/pypi/shade)
* python-jmespath / [jmespath](https://pypi.python.org/pypi/jmespath)
* python-dns / [dnspython](https://pypi.python.org/pypi/dnspython)
* Become (sudo) is not required.

### Optional Dependencies for localhost
**Note**: When using rhel images, `rhel-7-server-openstack-10-rpms` repository is required in order to install these packages.

* `python-openstackclient`
* `python-heatclient`

## Dependencies for OpenStack hosted cluster nodes (servers)

There are no additional dependencies for the cluster nodes. Required
configuration steps are done by Heat given a specific user data config
that normally should not be changed.

## Required galaxy modules

In order to pull in external dependencies for DNS configuration steps,
the following commads need to be executed:

    ansible-galaxy install \
      -r openshift-ansible-contrib/playbooks/provisioning/openstack/galaxy-requirements.yaml \
      -p openshift-ansible-contrib/roles

Alternatively you can install directly from github:

    ansible-galaxy install git+https://github.com/redhat-cop/infra-ansible,master \
      -p openshift-ansible-contrib/roles

Notes:
* This assumes we're in the directory that contains the clonned
openshift-ansible-contrib repo in its root path.
* When trying to install a different version, the previous one must be removed first
(`infra-ansible` directory from [roles](https://github.com/openshift/openshift-ansible-contrib/tree/master/roles)).
Otherwise, even if there are differences between the two versions, installation of the newer version is skipped.

## What does it do

* Create Nova servers with floating IP addresses attached
* Assigns Cinder volumes to the servers
* Set up an `openshift` user with sudo privileges
* Optionally attach Red Hat subscriptions
* Set up a bind-based DNS server
* When deploying more than one master, set up a HAproxy server


## Set up

### Copy the sample inventory

    cp -r openshift-ansible-contrib/playbooks/provisioning/openstack/sample-inventory inventory

### Copy ansible config

    cp openshift-ansible-contrib/playbooks/provisioning/openstack/sample-inventory/ansible.cfg ansible.cfg

### Update `inventory/group_vars/all.yml`

Pay special attention to the values in the first paragraph -- these
will depend on your OpenStack environment.

The `env_id` and `public_dns_domain` will form the cluster's DNS domain all
your servers will be under. With the default values, this will be
`openshift.example.com`. For workloads, the default subdomain is 'apps'.
That sudomain can be set as well by the `openshift_app_domain` variable in
the inventory.

The `openstack_<role name>_hostname` is a set of variables used for customising
hostnames of servers with a given role. When such a variable stays commented,
default hostname (usually the role name) is used.

The `public_dns_nameservers` is a list of DNS servers accessible from all
the created Nova servers. These will be serving as your DNS forwarders for
external FQDNs that do not belong to the cluster's DNS domain and its subdomains.

The `openshift_use_dnsmasq` controls either dnsmasq is deployed or not.
By default, dnsmasq is deployed and comes as the hosts' /etc/resolv.conf file
first nameserver entry that points to the local host instance of the dnsmasq
daemon that in turn proxies DNS requests to the authoritative DNS server.
When Network Manager is enabled for provisioned cluster nodes, which is
normally the case, you should not change the defaults and always deploy dnsmasq.

Note that the authoritative DNS server is configured on post provsision
steps, and the Neutron subnet for the Heat stack is updated to point to that
server in the end. So the provisioned servers will start using it natively
as a default nameserver that comes from the NetworkManager and cloud-init.

`openstack_ssh_key` is a Nova keypair - you can see your keypairs with
`openstack keypair list`. This guide assumes that its corresponding private
key is `~/.ssh/openshift`, stored on the ansible admin (control) node.

`openstack_default_image_name` is the default name of the Glance image the
servers will use. You can see your images with `openstack image list`.
In order to set a different image for a role, uncomment the line with the
corresponding variable (e.g. `openstack_lb_image_name` for load balancer) and
set its value to another available image name. `openstack_default_image_name`
must stay defined as it is used as a default value for the rest of the roles.

`openstack_default_flavor` is the default Nova flavor the servers will use.
You can see your flavors with `openstack flavor list`.
In order to set a different flavor for a role, uncomment the line with the
corresponding variable (e.g. `openstack_lb_flavor` for load balancer) and
set its value to another available flavor. `openstack_default_flavor` must
stay defined as it is used as a default value for the rest of the roles.

`openstack_external_network_name` is the name of the Neutron network
providing external connectivity. It is often called `public`,
`external` or `ext-net`. You can see your networks with `openstack
network list`.

`openstack_private_network_name` is the name of the private Neutron network
providing admin/control access for ansible. It can be merged with other
cluster networks, there are no special requirements for networking.

The `openstack_num_masters`, `openstack_num_infra` and
`openstack_num_nodes` values specify the number of Master, Infra and
App nodes to create.

The `openshift_cluster_node_labels` defines custom labels for your openshift
cluster node groups. It currently supports app and infra node groups.
The default value of this variable sets `region: primary` to app nodes and
`region: infra` to infra nodes.
An example of setting a customised label:
```
openshift_cluster_node_labels:
  app:
    mylabel: myvalue
```

The `openstack_nodes_to_remove` allows you to specify the numerical indexes
of App nodes that should be removed; for example, ['0', '2'],

The `docker_volume_size` is the default Docker volume size the servers will use.
In order to set a different volume size for a role,
uncomment the line with the corresponding variable (e. g. `docker_master_volume_size`
for master) and change its value. `docker_volume_size` must stay defined as it is
used as a default value for some of the servers (master, infra, app node).
The rest of the roles (etcd, load balancer, dns) have their defaults hard-coded.

**Note**: If the `ephemeral_volumes` is set to `true`, the `*_volume_size` variables
will be ignored and the deployment will not create any cinder volumes.

The `openstack_flat_secgrp`, controls Neutron security groups creation for Heat
stacks. Set it to true, if you experience issues with sec group rules
quotas. It trades security for number of rules, by sharing the same set
of firewall rules for master, node, etcd and infra nodes.

The `required_packages` variable also provides a list of the additional
prerequisite packages to be installed before to deploy an OpenShift cluster.
Those are ignored though, if the `manage_packages: False`.

The `openstack_inventory` controls either a static inventory will be created after the
cluster nodes provisioned on OpenStack cloud. Note, the fully dynamic inventory
is yet to be supported, so the static inventory will be created anyway.

The `openstack_inventory_path` points the directory to host the generated static inventory.
It should point to the copied example inventory directory, otherwise ti creates
a new one for you.

#### Multi-master configuration

Please refer to the official documentation for the
[multi-master setup](https://docs.openshift.com/container-platform/3.6/install_config/install/advanced_install.html#multiple-masters)
and define the corresponding [inventory
variables](https://docs.openshift.com/container-platform/3.6/install_config/install/advanced_install.html#configuring-cluster-variables)
in `inventory/group_vars/OSEv3.yml`. For example, given a load balancer node
under the ansible group named `ext_lb`:

    openshift_master_cluster_method: native
    openshift_master_cluster_hostname: "{{ groups.ext_lb.0 }}"
    openshift_master_cluster_public_hostname: "{{ groups.ext_lb.0 }}"

#### Security notes

Configure required `*_ingress_cidr` variables to restrict public access
to provisioned servers from your laptop (a /32 notation should be used)
or your trusted network. The most important is the `node_ingress_cidr`
that restricts public access to the deployed DNS server and cluster
nodes' ephemeral ports range.

Note, the command ``curl https://api.ipify.org`` helps fiding an external
IP address of your box (the ansible admin node).

There is also the `manage_packages` variable (defaults to True) you
may want to turn off in order to speed up the provisioning tasks. This may
be the case for development environments. When turned off, the servers will
be provisioned omitting the ``yum update`` command. This brings security
implications though, and is not recommended for production deployments.

### Configure the OpenShift parameters

Finally, you need to update the DNS entry in
`inventory/group_vars/OSEv3.yml` (look at
`openshift_master_default_subdomain`).

In addition, this is the place where you can customise your OpenShift
installation for example by specifying the authentication.

The full list of options is available in this sample inventory:

https://github.com/openshift/openshift-ansible/blob/master/inventory/byo/hosts.ose.example

Note, that in order to deploy OpenShift origin, you should update the following
variables for the `inventory/group_vars/OSEv3.yml`, `all.yml`:

    deployment_type: origin
    openshift_deployment_type: "{{ deployment_type }}"

### Configure static inventory and access via a bastion node

Example inventory variables:

    openstack_use_bastion: true
    bastion_ingress_cidr: "{{openstack_subnet_prefix}}.0/24"
    openstack_private_ssh_key: ~/.ssh/openshift
    openstack_inventory: static
    openstack_inventory_path: ../../../../inventory
    openstack_ssh_config_path: /tmp/ssh.config.openshift.ansible.openshift.example.com

The `openstack_subnet_prefix` is the openstack private network for your cluster.
And the `bastion_ingress_cidr` defines accepted range for SSH connections to nodes
additionally to the `ssh_ingress_cidr`` (see the security notes above).

The SSH config will be stored on the ansible control node by the
gitven path. Ansible uses it automatically. To access the cluster nodes with
that ssh config, use the `-F` prefix, f.e.:

    ssh -F /tmp/ssh.config.openshift.ansible.openshift.example.com master-0.openshift.example.com echo OK

Note, relative paths will not work for the `openstack_ssh_config_path`, but it
works for the `openstack_private_ssh_key` and `openstack_inventory_path`. In this
guide, the latter points to the current directory, where you run ansible commands
from.

To verify nodes connectivity, use the command:

    ansible -v -i inventory/hosts -m ping all

If something is broken, double-check the inventory variables, paths and the
generated `<openstack_inventory_path>/hosts` and `openstack_ssh_config_path` files.

The `inventory: dynamic` can be used instead to access cluster nodes directly via
floating IPs. In this mode you can not use a bastion node and should specify
the dynamic inventory file in your ansible commands , like `-i openstack.py`.

## Deployment

### Run the playbook

Assuming your OpenStack (Keystone) credentials are in the `keystonerc`
this is how you stat the provisioning process from your ansible control node:

    . keystonerc
    ansible-playbook openshift-ansible-contrib/playbooks/provisioning/openstack/provision.yaml

Note, here you start with an empty inventory. The static inventory will be populated
with data so you can omit providing additional arguments for future ansible commands.

If bastion enabled, the generates SSH config must be applied for ansible.
Otherwise, it is auto included by the previous step. In order to execute it
as a separate playbook, use the following command:

    ansible-playbook openshift-ansible-contrib/playbooks/provisioning/openstack/post-provision-openstack.yml

The first infra node then becomes a bastion node as well and proxies access
for future ansible commands. The post-provision step also configures Satellite,
if requested, and DNS server, and ensures other OpenShift requirements to be met.

### Running Custom Post-Provision Actions

If you'd like to run post-provision actions, you can do so by creating a custom playbook. Here's one example that adds additional YUM repositories:

```
---
- hosts: app
  tasks:

  # enable EPL
  - name: Add repository
    yum_repository:
      name: epel
      description: EPEL YUM repo
      baseurl: https://download.fedoraproject.org/pub/epel/$releasever/$basearch/
```

This example runs against app nodes. The list of options include:

  - cluster_hosts (all hosts: app, infra, masters, dns, lb)
  - OSEv3 (app, infra, masters)
  - app
  - dns
  - masters
  - infra_hosts

After writing your custom playbook, run it like this:

```
ansible-playbook --private-key ~/.ssh/openshift -i myinventory/ custom-playbook.yaml
```

If you'd like to limit the run to one particular host, you can do so as follows:

```
ansible-playbook --private-key ~/.ssh/openshift -i myinventory/ custom-playbook.yaml -l app-node-0.openshift.example.com
```

### Install OpenShift

Once it succeeds, you can install openshift by running:

    ansible-playbook openshift-ansible/playbooks/byo/config.yml

### Access UI

OpenShift UI may be accessed via the 1st master node FQDN, port 8443.

When using a bastion, you may want to make an SSH tunnel from your control node
to access UI on the `https://localhost:8443`, with this inventory variable:

   openshift_ui_ssh_tunnel: True

Note, this requires sudo rights on the ansible control node and an absolute path
for the `openstack_private_ssh_key`. You should also update the control node's
`/etc/hosts`:

    127.0.0.1 master-0.openshift.example.com

In order to access UI, the ssh-tunnel service will be created and started on the
control node. Make sure to remove these changes and the service manually, when not
needed anymore.

## License

As the rest of the openshift-ansible-contrib repository, the code here is
licensed under Apache 2.
