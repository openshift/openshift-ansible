# OpenStack Provisioning

This repository contains playbooks and Heat templates to provision
OpenStack resources (servers, networking, volumes, security groups,
etc.). The result is an environment ready for openshift-ansible.

## Dependencies for localhost (ansible control/admin node)

* [Ansible 2.3](https://pypi.python.org/pypi/ansible)
* [Ansible-galaxy](https://pypi.python.org/pypi/ansible-galaxy-local-deps)
* [jinja2](http://jinja.pocoo.org/docs/2.9/)
* [shade](https://pypi.python.org/pypi/shade)
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

Note, this assumes we're in the directory that contains the clonned
openshift-ansible-contrib repo in its root path.

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

### Copy clouds.yaml

    cp openshift-ansible-contrib/playbooks/provisioning/openstack/sample-inventory/clouds.yaml clouds.yaml

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

`openstack_ssh_key` is a Nova keypair -- you can see your keypairs with
`openstack keypair list`.

`openstack_default_image_name` is the name of the Glance image the
servers will use. You can
see your images with `openstack image list`.

`openstack_default_flavor` is the Nova flavor the servers will use.
You can see your flavors with `openstack flavor list`.

`openstack_external_network_name` is the name of the Neutron network
providing external connectivity. It is often called `public`,
`external` or `ext-net`. You can see your networks with `openstack
network list`.

The `openstack_num_masters`, `openstack_num_infra` and
`openstack_num_nodes` values specify the number of Master, Infra and
App nodes to create.

The `openstack_nodes_to_remove` allows you to specify the numerical indexes
of App nodes that should be removed; for example, ['0', '2'],

The `openstack_flat_secgrp`, controls Neutron security groups creation for Heat
stacks. Set it to true, if you experience issues with sec group rules
quotas. It trades security for number of rules, by sharing the same set
of firewall rules for master, node, etcd and infra nodes.

The `required_packages` variable also provides a list of the additional
prerequisite packages to be installed before to deploy an OpenShift cluster.
Those are ignored though, if the `manage_packages: False`.

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

### Update the DNS names in `inventory/hosts`

The different server groups are currently grouped by the domain name,
so if you end up using a different domain than
`openshift.example.com`, you will need to update the `inventory/hosts`
file.

For example, if your final domain is `my.cloud.com`, you can run this
command to fix update the `hosts` file:

    sed -i 's/openshift.example.com/my.cloud.com/' inventory/hosts

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
    origin_release: 1.5.1
    openshift_deployment_type: "{{ deployment_type }}"

## Deployment

### Run the playbook

Assuming your OpenStack (Keystone) credentials are in the `keystonerc`
file, this is how you stat the provisioning process:

    . keystonerc
    ansible-playbook -i inventory --timeout 30  --private-key ~/.ssh/openshift openshift-ansible-contrib/playbooks/provisioning/openstack/provision.yaml

### Install OpenShift

Once it succeeds, you can install openshift by running:

    ansible-playbook --user openshift --private-key ~/.ssh/openshift -i inventory/ openshift-ansible/playbooks/byo/config.yml


## License

As the rest of the openshift-ansible-contrib repository, the code here is
licensed under Apache 2. However, the openstack.py file under
`sample-inventory` is GPLv3+. See the INVENTORY-LICENSE.txt file for the full
text of the license.
