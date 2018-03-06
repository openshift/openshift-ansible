# OpenStack Provisioning

This directory contains [Ansible][ansible] playbooks and roles to create
OpenStack resources (servers, networking, volumes, security groups,
etc.). The result is an environment ready for OpenShift installation
via [openshift-ansible].

We provide everything necessary to be able to install OpenShift on
OpenStack (including the load balancer servers when necessary). In addition,
we work on providing integration with the OpenStack-native services (storage,
lbaas, baremetal as a service, dns, etc.).


## Requirements

In order to run these Ansible playbooks, you'll need an Ansible host and an
OpenStack environment.

### Ansible Host

Start by choosing a host from which you'll run [Ansible][ansible]. This can
be the computer you read this guide on or an OpenStack VM you'll create
specifically for this purpose.

The required dependencies for the Ansible host are:

* [Ansible](https://pypi.python.org/pypi/ansible) version >=2.4.1
* [jinja2](http://jinja.pocoo.org/docs/2.9/) version >= 2.10
* [shade](https://pypi.python.org/pypi/shade) version >= 1.26
* python-jmespath / [jmespath](https://pypi.python.org/pypi/jmespath)
* python-dns / [dnspython](https://pypi.python.org/pypi/dnspython)
* Become (sudo) is *not* required.

Optional dependencies include:

* `python-openstackclient`
* `python-heatclient`

**Note**: If you're using RHEL images, the `rhel-7-server-openstack-10-rpms`
repository is required in order to install these openstack clients.

Clone the [openshift-ansible][openshift-ansible] repository:

```
$ git clone https://github.com/openshift/openshift-ansible
```

### OpenStack Environment

Before you start the installation, you'll need an OpenStack environment.
Options include:

* [Devstack][devstack]
* [Packstack][packstack]
* [TripleO][tripleo] **Overcloud**

You can also use a public cloud or an OpenStack within your organization.

The OpenStack environment must satisfy these requirements:

* It must be Newton (equivalent to Red hat OpenStack 10) or newer
* Heat (Orchestration) must be available
* The deployment image (CentOS 7.4 or RHEL 7) must be loaded
* The deployment flavor must be available to your user
  - `m1.medium` / 4GB RAM + 40GB disk should be enough for testing
  - look at
    the [Minimum Hardware Requirements page][hardware-requirements]
    for production
* The keypair for SSH must be available in OpenStack
* `keystonerc` file that lets you talk to the OpenStack services
   * NOTE: only Keystone V2 is currently supported

You may also optionally want:

* External Neutron network with a floating IP address pool


## Configuration

Configuration is done through an Ansible inventory directory. You can switch
between multiple inventories to test multiple configurations.

Start by copying the sample inventory to your inventory directory.

```
$ cp -r openshift-ansible/playbooks/openstack/sample-inventory/ inventory
```

The sample inventory contains defaults that will do the following:

* create VMs for an OpenShift cluster with 1 Master node, 1 Infra node, and 2 App nodes
* create a new Neutron network and assign floating IP addresses to the VMs

You may have to perform further configuration in order to match the inventory
to your environment.

### OpenStack Configuration

The OpenStack configuration file is `inventory/group_vars/all.yml`.

Open the file and plug in the image, flavor and network configuration
corresponding to your OpenStack installation.

```bash
$ vi inventory/group_vars/all.yml
```

* `openshift_openstack_keypair_name` Set your OpenStack keypair name.
   - See `openstack keypair list` to find the keypairs registered with
   OpenShift.
   - This must correspond to your private SSH key in `~/.ssh/id_rsa`
* `openshift_openstack_external_network_name` Set the floating IP
   network of your OpenStack.
   - See `openstack network list` for the list of networks.
   - Often called `public`, `external` or `ext-net`.
* `openshift_openstack_default_image_name` Set the image you want your
   OpenShift VMs to run.
   - See `openstack image list` for the list of available images.
* `openshift_openstack_default_flavor` Set the flavor you want your
   OpenShift VMs to use.
   - See `openstack flavor list` for the list of available flavors.


### OpenShift Configuration

The OpenShift configuration file is `inventory/group_vars/OSEv3.yml`.

The default options will mostly work, but openshift-ansible's hardware check
may fail unless you specified a large flavor suitable for a production-ready
environment.

You can disable those checks by adding this line to `inventory/group_vars/OSEv3.yml`:

```yaml
openshift_disable_check: disk_availability,memory_availability,docker_storage
```

**Important**: The default authentication method will allow **any username
and password** in! If you're running this in a public place, you need
to set up access control.

Feel free to look at
the [Sample OpenShift Inventory][sample-openshift-inventory] and
the [configuration][configuration].

### Advanced Configuration

The [Configuration page][configuration] details several
additional options. These include:

* Set Up Authentication (TODO)
* [Multiple Masters with a load balancer][loadbalancer]
* [External Dns][external-dns]
* Multiple Clusters (TODO)
* [Cinder Registry][cinder-registry]

Read the [Configuration page][configuration] for a full listing of
configuration options.


## Installation

Before running the installation playbook, you may want to create an `ansible.cfg`
file with useful defaults:

```bash
$ cp openshift-ansible/ansible.cfg ansible.cfg
```

We recommend adding an additional option:

```cfg
any_errors_fatal = true
```

This will abort the Ansible playbook execution as soon as any error is
encountered.

Now, run the provision + install playbook. This will create OpenStack resources
and deploy an OpenShift cluster on top of them:

```bash
$ ansible-playbook --user openshift \
  -i openshift-ansible/playbooks/openstack/inventory.py \
  -i inventory \
  openshift-ansible/playbooks/openstack/openshift-cluster/provision_install.yml
```

* If you're using multiple inventories, make sure you pass the path to
the right one to `-i`.
* If your SSH private key is not in `~/.ssh/id_rsa`, use the `--private-key`
option to specify the correct path.
* Note that we must pass in the [dynamic inventory][dynamic] --
`openshift-ansible/playbooks/openstack/inventory.py`. This is a script that
looks for OpenStack resources and enables Ansible to reference them.


## Post-Install

Once installation completes, a few additional steps may be required or useful.

### Configure DNS

OpenShift requires two public DNS records to function fully. The first one points to
the master/load balancer and provides the UI/API access. The other one is a
wildcard domain that resolves app route requests to the infra node. A private DNS
server and records are not required and not managed here.

If you followed the default installation from the README section, there is no
DNS configured. You should add two entries to the `/etc/hosts` file on the
Ansible host (where you to do a quick validation. A real deployment will
however require a DNS server with the following entries set.

First, run the `openstack server list` command and note the floating IP
addresses of the *master* and *infra* nodes (we will use `10.40.128.130` for
master and `10.40.128.134` for infra here).

Then add the following entries to your `/etc/hosts`:

```
10.40.128.130 console.openshift.example.com
10.40.128.134 cakephp-mysql-example-test.apps.openshift.example.com
```

This points the cluster domain (as defined in the
`openshift_master_cluster_public_hostname` Ansible variable in `OSEv3`) to the
master node and any routes for deployed apps to the infra node.

If you deploy another app, it will end up with a different URL (e.g.
myapp-test.apps.openshift.example.com) and you will need to add that too.  This
is why a real deployment should always run a DNS where the second entry will be
a wildcard `*.apps.openshift.example.com).

This will be sufficient to validate the cluster here.

Take a look at the [External DNS](#dns-configuration-variables) section for
configuring a DNS service.


### Get the `oc` Client

The OpenShift command line client (called `oc`) can be downloaded and extracted
from `openshift-origin-client-tools` on the OpenShift release page:

https://github.com/openshift/origin/releases/latest/

You can also copy it from the master node:

    $ ansible -i inventory masters[0] -m fetch -a "src=/bin/oc dest=oc"

Once you obtain the `oc` binary, remember to put it in your `PATH`.


### Logging in Using the Command Line

```
oc login --insecure-skip-tls-verify=true https://master-0.openshift.example.com:8443 -u user -p password
oc new-project test
oc new-app --template=cakephp-mysql-example
oc status -v
curl http://cakephp-mysql-example-test.apps.openshift.example.com
```

This will trigger an image build. You can run `oc logs -f
bc/cakephp-mysql-example` to follow its progress.

Wait until the build has finished and both pods are deployed and running:

```
$ oc status -v
In project test on server https://master-0.openshift.example.com:8443

http://cakephp-mysql-example-test.apps.openshift.example.com (svc/cakephp-mysql-example)
  dc/cakephp-mysql-example deploys istag/cakephp-mysql-example:latest <-
    bc/cakephp-mysql-example source builds https://github.com/openshift/cakephp-ex.git on openshift/php:7.0
    deployment #1 deployed about a minute ago - 1 pod

svc/mysql - 172.30.144.36:3306
  dc/mysql deploys openshift/mysql:5.7
    deployment #1 deployed 3 minutes ago - 1 pod

Info:
  * pod/cakephp-mysql-example-1-build has no liveness probe to verify pods are still running.
    try: oc set probe pod/cakephp-mysql-example-1-build --liveness ...
View details with 'oc describe <resource>/<name>' or list everything with 'oc get all'.

```

You can now look at the deployed app using its route:

```
$ curl http://cakephp-mysql-example-test.apps.openshift.example.com
```

Its `title` should say: "Welcome to OpenShift".


### Accessing the UI

You can access the OpenShift cluster with a web browser by going to:

https://master-0.openshift.example.com:8443

Note that for this to work, the OpenShift nodes must be accessible
from your computer and its DNS configuration must use the cluster's
DNS.

### Running Custom Post-Provision Actions

A custom playbook can be run like this:

```
ansible-playbook --private-key ~/.ssh/openshift -i inventory/ openshift-ansible-contrib/playbooks/provisioning/openstack/custom-actions/custom-playbook.yml
```

If you'd like to limit the run to one particular host, you can do so as follows:

```
ansible-playbook --private-key ~/.ssh/openshift -i inventory/ openshift-ansible-contrib/playbooks/provisioning/openstack/custom-actions/custom-playbook.yml -l app-node-0.openshift.example.com
```

You can also create your own custom playbook. Here are a few examples:

#### Adding additional YUM repositories

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

#### Attaching additional RHN pools

```
---
- hosts: cluster_hosts
  tasks:
  - name: Attach additional RHN pool
    become: true
    command: "/usr/bin/subscription-manager attach --pool=<pool ID>"
    register: attach_rhn_pool_result
    until: attach_rhn_pool_result.rc == 0
    retries: 10
    delay: 1
```

This playbook runs against all cluster nodes. In order to help prevent slow connectivity
problems, the task is retried 10 times in case of initial failure.
Note that in order for this example to work in your deployment, your servers must use the RHEL image.

#### Adding extra Docker registry URLs

This playbook is located in the [custom-actions](https://github.com/openshift/openshift-ansible-contrib/tree/master/playbooks/provisioning/openstack/custom-actions) directory.

It adds URLs passed as arguments to the docker configuration program.
Going into more detail, the configuration program (which is in the YAML format) is loaded into an ansible variable
([lines 27-30](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions/add-docker-registry.yml#L27-L30))
and in its structure, `registries` and `insecure_registries` sections are expanded with the newly added items
([lines 56-76](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions/add-docker-registry.yml#L56-L76)).
The new content is then saved into the original file
([lines 78-82](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions/add-docker-registry.yml#L78-L82))
and docker is restarted.

Example usage:
```
ansible-playbook -i <inventory> openshift-ansible-contrib/playbooks/provisioning/openstack/custom-actions/add-docker-registry.yml  --extra-vars '{"registries": "reg1", "insecure_registries": ["ins_reg1","ins_reg2"]}'
```

#### Adding extra CAs to the trust chain

This playbook is also located in the [custom-actions](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions) directory.
It copies passed CAs to the trust chain location and updates the trust chain on each selected host.

Example usage:
```
ansible-playbook -i <inventory> openshift-ansible-contrib/playbooks/provisioning/openstack/custom-actions/add-cas.yml --extra-vars '{"ca_files": [<absolute path to ca1 file>, <absolute path to ca2 file>]}'
```

Please consider contributing your custom playbook back to openshift-ansible-contrib!

A library of custom post-provision actions exists in `openshift-ansible-contrib/playbooks/provisioning/openstack/custom-actions`. Playbooks include:

* [add-yum-repos.yml](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions/add-yum-repos.yml): adds a list of custom yum repositories to every node in the cluster
* [add-rhn-pools.yml](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions/add-rhn-pools.yml): attaches a list of additional RHN pools to every node in the cluster
* [add-docker-registry.yml](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions/add-docker-registry.yml): adds a list of docker registries to the docker configuration on every node in the cluster
* [add-cas.yml](https://github.com/openshift/openshift-ansible-contrib/blob/master/playbooks/provisioning/openstack/custom-actions/add-rhn-pools.yml): adds a list of CAs to the trust chain on every node in the cluster


### Scale Deployment up/down

#### Scaling up

One can scale up the number of application nodes by executing the ansible playbook
`openshift-ansible-contrib/playbooks/provisioning/openstack/scale-up.yaml`.
This process can be done even if there is currently no deployment available.
The `increment_by` variable is used to specify by how much the deployment should
be scaled up (if none exists, it serves as a target number of application nodes).
The path to `openshift-ansible` directory can be customised by the `openshift_ansible_dir`
variable. Its value must be an absolute path to `openshift-ansible` and it cannot
contain the '/' symbol at the end.

Usage:

```
ansible-playbook -i <path to inventory> openshift-ansible-contrib/playbooks/provisioning/openstack/scale-up.yaml` [-e increment_by=<number>] [-e openshift_ansible_dir=<path to openshift-ansible>]
```


## Uninstall

Everything in the cluster is contained within a Heat stack. To
completely remove the cluster and all the related OpenStack resources,
run this command:

```bash
openstack stack delete --wait --yes openshift.example.com
```

[ansible]: https://www.ansible.com/
[openshift-ansible]: https://github.com/openshift/openshift-ansible
[openshift-ansible-setup]: https://github.com/openshift/openshift-ansible#setup
[devstack]: https://docs.openstack.org/devstack/
[tripleo]: http://tripleo.org/
[packstack]: https://www.rdoproject.org/install/packstack/
[control-host-image]: https://hub.docker.com/r/redhatcop/control-host-openstack/
[hardware-requirements]: https://docs.openshift.org/latest/install_config/install/prerequisites.html#hardware
[origin]: https://www.openshift.org/
[centos7]: https://www.centos.org/
[sample-openshift-inventory]: https://github.com/openshift/openshift-ansible/blob/master/inventory/hosts.example
[configuration]: ./configuration.md
[loadbalancer]: ./configuration.md#multi-master-configuration
[external-dns]: ./configuration.md#dns-configuration
[cinder-registry]: ./configuration.md#cinder-backed-registry-configuration
[dynamic]: http://docs.ansible.com/ansible/latest/intro_dynamic_inventory.html
