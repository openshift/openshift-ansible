# Couchbase Server with Ansible


               .CCCCC                       CCCCC.
              .CCCCCC                       CCCCCC.
              .CCCCCC                       CCCCCC.
              .CCCCCC                       CCCCCC.
              .CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC.
              .CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC.
              .CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC.
               .CCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCCC.

> **NOTE: This role is experimental and not intended for production use**.
> Feel free to use the role for evaluation, development, or testing, and
> definitely borrow the ideas contained within for your own production role
> or playbooks. As with other Couchbase Labs projects, this is primarily
> for experimentation.

[Couchbase Server](http://www.couchbase.com/couchbase-server/overview) is a
high performance NoSQL document database available in Community and Enterprise
editions for several operating system environments.

This project provides documentation and a collection of scripts to help you
automate the deployment of Couchbase Server Enterprise Edition using
[Ansible](http://www.ansibleworks.com/). These are the instructions for
deploying a development cluster with Vagrant and VirtualBox.

## Vagrant Development Cluster

In some situations deploying a small virtualized cluster on your local
development machine can be handy. This document describes such a with the
following software:

* [Couchbase Server](http://www.couchbase.com/couchbase-server/overview)
* [VirtualBox](https://www.virtualbox.org/)
* [Vagrant](http://www.vagrantup.com/) with Ansible provisioner and
  supporting plugin
* [Ansible](http://www.ansibleworks.com/)

Each of the virtual machines are configured with 1.5GB RAM, 2 CPU cores, and
2 network interfaces. The first interface uses NAT and has connection via the
host to the outside world. The second interface is a private network and is
used for intra-cluster communication in addition to access from the host
machine to Couchbase Server's administration and API ports.

The Vagrant configuration file (`Vagrantfile`) is responsible for
configuring the virtual machines and a baseline OS installation.

The Ansible playbooks then further refine OS configuration, Couchbase Server
package download and installation, and the initialization of the 3 nodes
into a ready to use cluster.

## Works with Ansible Galaxy

This role is designed to be installed via the `ansible-galaxy` command
instead of being directly run from the git repository.

You should install it like this:

```
ansible-galaxy install couchbase.couchbase-server
```

You'll want to make sure you have write access to `/etc/ansible/roles/` since
that is where the role will be installed by default, or define your own
Ansible role path by creating a `$HOME/.ansible.cfg` file with these contents:

```
[defaults]
roles_path = PATH_TO_ROLES
```

Change `PATH_TO_ROLES` to a directory that you 
have write access to.

## Quick Start

Begin from the top level directory of this project and use the following
5 steps to get up and running:

1. Install [VirtualBox](https://www.virtualbox.org/wiki/Downloads), 
   [Vagrant](http://downloads.vagrantup.com/), 
   [vagrant-hosts](https://github.com/adrienthebo/vagrant-hosts), 
   and [Ansible](http://www.ansibleworks.com/docs/intro_installation.html#latest-releases-via-pip).
2. Edit `/etc/hosts` or use the included `bin/preinstall` script to add
   the following entries to your development system's `/etc/hosts` file:
 * 10.1.42.10 cb1.local cb1
 * 10.1.42.20 cb2.local cb2
 * 10.1.42.30 cb3.local cb3
3. `cd $PATH_TO_ROLES/couchbase.couchbase-server/examples`
4. `vagrant up`
5. Access the cluster at http://cb1:8091 with username **Administrator**
   and password **couchbase**.

By default, this project will install CentOS 6.5 based cluster nodes. If you
prefer, it can also install Ubuntu 12.04 based nodes by changing the command
in step 4 to the following:

```
BOX_NAME="ubuntu/precise64" vagrant up
```

If you'd like to follow a more detailed installation process with additional
explanation of the steps and technologies, see the following sections of
this guide.

## Prerequisites

Before you begin with the steps in this guide, please ensure that you have
the following prerequisites configured and installed.

### Networking

Ensure that your host machine can access the internet so that the required
software can be downloaded as needed. This includes both downloading the
prerequisite software, the VirtualBox operating system image, and Couchbase
Server itself.

You'll also need to resolve the node VM host names to their default IP
addresses. This can be most easily done by adding the following lines to
the `/etc/hosts` file on the host machine:

```
10.1.42.10 cb1.local cb1
10.1.42.20 cb2.local cb2
10.1.42.30 cb3.local cb3
```

A convenience script, `bin/preinstall` is provided to automate this step
and some other steps for you.

### VirtualBox

VirtualBox is a freely available virtualization product that supports various
operating system guests running in virtual machines on Mac OS X. Download and
install the latest version from the [VirtualBox website](https://www.virtualbox.org/wiki/Downloads) before proceeding with
the rest of the steps in this section.

### Vagrant and Plugins

Vagrant helps automate building complete development environments on Mac OS X
with the notion of *providers* for different deployment targets like
VirtualBox and *provisioners* like Ansible for handling the actual deployment
and provisioning of the virtual machines.

This guide uses Vagrant along with a supporting plugin to automate the
creation of the VirtualBox machines which we will be using for the
Couchbase Server nodes.

The plugin used in this project is 
[Vagrant hosts](https://github.com/adrienthebo/vagrant-hosts), which is used
for adding hostname information to the `/etc/hosts` file on each virtual 
machine. This is required prior to the execution of Ansible playbooks so 
that Ansible will function properly over SSH.

Visit the Vagrant [downloads page](http://downloads.vagrantup.com/) to get the
appropriate version, and proceed with installation of the package. After you
have installed Vagrant, open a terminal and execute the following shell
commands to install the supporting plugins:

```
vagrant plugin install vagrant-hosts
```

These commands should return success messages; provided that the commands are
successful, you can continue with the rest of the steps in this guide.

### Ansible

Install Ansible for Mac OS X using `pip` based on the
[installation documentation](http://www.ansibleworks.com/docs/intro_installation.html#latest-releases-via-pip). The steps are simple:

```
sudo easy_install pip
sudo pip install ansible
```

## Bootstrap the Cluster

Now it's time for bootstrapping the Couchbase Server cluster.

There are some environment variables which you set to alter basic details
about the Vagrant based setup; the defaults are in parentheses:

* ANSIBLE_PLAYBOOK (cluster_init.yml) playbook executed by Ansible provisioner
* BOX_MEM (1536) specifies virtual machine RAM in megabytes
* BOX_NAME (ubuntu/trusty64) specifies name of the Vagrant box to use
* CLUSTER_HOSTS (vagrant_hosts) specifies Ansible hosts inventory file

Open a terminal, change into the *examples* subdirectory of this role's
root directory and execute the Ansible playbook:

```
cd $ROLESPATH/couchbase.couchbase-server/examples
vagrant up
```

Yep, that's all there is to it.

One command and a bit of patience while Vagrant and Ansible work their magic.

If bootstrapping a cluster for the first time, you will be prompted to accept
the host key information for each node VM by ssh; be sure to answer **yes**
to these prompts.

### Debian

By default, this project will install CentOS 6.5 based cluster nodes. If you
prefer, you can install Debian 7.4 based nodes by changing the
`vagrant up` command to the following:

```
BOX_NAME="chef/debian-7.4" vagrant up
```

### Ubuntu

By default, this project will install CentOS 6.5 based cluster nodes. If you
prefer, you can install Ubuntu 12.04 based nodes by changing the
`vagrant up` command to the following:

```
BOX_NAME="ubuntu/precise64" vagrant up
```

## Give it a Try

Once the Ansible playbooks complete without error, you can open a browser and
access the primary Couchbase Server cluster node at the following URL:

```
http://cb1:8091
```

The administrator username and password as configured by this project
are:

* Username: **Administrator**
* Password: **couchbase**

Once you've logged in and verified that the cluster is available, you're now
ready to create buckets and begin using your new Couchbase Server development
cluster.

### Other Operations

While the basic instructions for getting started do a fair bit of work, you
can also run the `cluster_init.yml` playbook to only perform the cluster
initialization.

You can also run a subset of the tasks independently through Ansible's
tag support; here is a list of available tags by role:

**bootstrap**

* *network* : Network hostname
* *system_packages* : Install any required system packages
* *system_tuning* : Set disk scheduler specified in `linux/group_vars/all`
  for the data and index volumes, disable Transparent Huge Pages, and
  other system tuning

**couchbase-server**

* *installation* : Download and install the Couchbase Server package
* *network* : Couchbase Server specific firewall settings
* *service* : Ensure that the Couchbase Server service is started

Here are some examples of tag usage:

Install required system packages, such as *libselinux-python* on CentOS:

```
ansible-playbook -i vagrant_hosts cluster_install.yml --tags "system_packages"
```

Set the disk scheduler specified in `linux/group_vars/all` for the data
and index volumes, disable Transparent Huge Pages, and perform other system
tuning:

```
ansible-playbook -i vagrant_hosts cluster_install.yml --tags "system_tuning"
```

Download and install the version of Couchbase Server specified in either
`defaults/main.yml` or `vars/main.yml` for the Linux distribution in use:

```
ansible-playbook -i vagrant_hosts cluster_install.yml --tags "installation"
```

You can also combine multiple tags, as in the following example, which will
perform the system tuning and installation tasks:

```
ansible-playbook -i vagrant_hosts cluster_install.yml \
--tags "system_tuning, installation"
```
## Examples

The `examples` directory contains some basic playbooks, host inventory
examples, and Vagrant bits as follows:

* `cluster_backup.yml` full backup of cluster and retrieval of backup tarball
* `cluster_collect_info.yml` gathers cluster logs with `cbcollect_info`
* `cluster_init.yml` installs Couchbase Server and initializes the cluster
* `cluster_install.yml` prepares OS and installs Couchbase Server only
* `create_bucket.yml` creates an example bucket
* `load_bucket.yml` loads sample JSON data into a bucket
* `node_failover.yml` manual failover of cluster node
* `retreive_ssl_cert.yml` retrieve and store node's SSL certificate
* `site.yml` basic role inclusion example
* `example_hosts` example hosts inventory in format required by this project
* `Vagrantfile` example Vagrant development cluster definition
* `vagrant_hosts` default Vagrant hosts inventory file

### Create Bucket

The example playbook `create_bucket.yml` for bucket creation can be used
as follows:

Upon first execution without specifying variable arguments via the 
`ansible-playbook` extra vars ('-e') option, the playbook will generate a
bucket with the following properties:

* Bucket name: *default*
* Bucket type: *couchbase*
* Bucket port: *11211*
* Bucket RAM size: 256MB
* Bucket replica number: 1

If you'd like to create your own buckets, then use the `ansible-playbook`
extra vars ('-e') option and specify values for the
*b_name*, *b_type*, *b_port*, *b_ramsize*, and *b_replica* variables like so:

```
ansible-playbook -i vagrant_hosts create_bucket.yml \
-e "couchbase_server_bucket_name=danika couchbase_server_bucket_type_type=couchbase couchbase_server_bucket_port=11223 couchbase_server_bucket_ram=256 couchbase_server_bucket_replica=2"
```

or perhaps you'd like to make a memcached based bucket? No problem:

```
ansible-playbook -i vagrant_hosts create_bucket.yml \
-e "couchbase_server_bucket_name=breandon couchbase_server_bucket_type_type=memcached couchbase_server_bucket_port=11224 couchbase_server_bucket_ram=512 couchbase_server_bucket_replica=0"
```

## Notes

0. This project functions with the following software versions:
  * Ansible version 1.9.2
  * VirtualBox version 5.0.0
  * Vagrant version 1.7.3
  * Vagrant Hosts version 2.4.0
1. This project uses CentOS 6.5 and Ubuntu 12.04 by default as these are
   among the supported major versions of platforms which are listed on the
   Couchbase Server package downloads page
2. The `bin/preinstall` shell script performs the following actions for you:
 * Adds each node's host information to the host machine's `/etc/hosts`
 * Ensures the correct permissions on Vagrant SSH private key
 * Optionally installs the Vagrant hosts plugin
3. Review possible operating system tuning settings in the following files:
 * `roles/couchbase-server/templates/etc_sysctl.d_couchbase-server.conf.j2`
 * `roles/couchbase-server/templates/iptables.j2`

## References

1. http://www.couchbase.com/couchbase-server/overview
2. http://www.ansibleworks.com/
3. http://www.vagrantup.com/
4. https://www.virtualbox.org/
5. https://github.com/adrienthebo/vagrant-hosts
