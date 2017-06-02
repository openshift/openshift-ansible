# OpenStack Provisioning

This repository contains playbooks and Heat templates to provision
OpenStack resources (servers, networking, volumes, security groups,
etc.). The result is an environment ready for openshift-ansible.


## Dependencies

* [Ansible 2.3](https://pypi.python.org/pypi/ansible)
* [shade](https://pypi.python.org/pypi/shade)


## What does it do

* Create Nova servers with floating IP addresses attached
* Assigns Cinder volumes to the servers
* Set up an `openshift` user with sudo privileges
* Optionally attach Red Hat subscriptions
* Set up a bind-based DNS server
* When deploying more than one master, set up a HAproxy server


## Set up

### Copy the sample inventory

    cp openshift-ansible-contrib/playbooks/provisioning/openstack/sample-inventory inventory

### Copy clouds.yaml

    cp openshift-ansible-contrib/playbooks/provisioning/openstack/sample-inventory/clouds.yaml clouds.yaml

### Update `inventory/group_vars/all.yml`

Pay special attention to the values in the first paragraph -- these
will depend on your OpenStack environment.

The `env_id` and `openstack_dns_domain` will form the DNS domain all
your servers will be under. With the default values, this will be
`openshift.example.com`.

`openstack_nameservers` is a list of DNS servers accessible from all
the created Nova servers. These will be serve as your DNS forwarders.

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


## Deployment

### Run the playbook

Assuming your OpenStack (Keystone) credentials are in the `keystonerc`
file, this is how you stat the provisioning process:

    . keystonerc
    ansible-playbook -i inventory  --private-key ~/.ssh/openshift openshift-ansible-contrib/playbooks/provisioning/openstack/provision.yaml

### Install OpenShift

Once it succeeds, you can install openshift by running:

    ansible-playbook --become --user openshift --private-key ~/.ssh/openshift -i inventory/ openshift-ansible/playbooks/byo/config.yml


## License

As the rest of the openshift-ansible-contrib repository, the code here is
licensed under Apache 2. However, the openstack.py file under
`sample-inventory` is GPLv3+. See the INVENTORY-LICENSE.txt file for the full
text of the license.
