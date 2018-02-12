## Dependencies for localhost (ansible control/admin node)

* [Ansible](https://pypi.python.org/pypi/ansible) version >=2.4.0
* [jinja2](http://jinja.pocoo.org/docs/2.9/) version >= 2.10
* [shade](https://pypi.python.org/pypi/shade) version >= 1.26
* python-jmespath / [jmespath](https://pypi.python.org/pypi/jmespath)
* python-dns / [dnspython](https://pypi.python.org/pypi/dnspython)
* Become (sudo) is not required.

**NOTE**: You can use a Docker image with all dependencies set up.
Find more in the [Deployment section](#deployment).

### Optional Dependencies for localhost
**Note**: When using rhel images, `rhel-7-server-openstack-10-rpms` repository is required in order to install these packages.

* `python-openstackclient`
* `python-heatclient`

## Dependencies for OpenStack hosted cluster nodes (servers)

There are no additional dependencies for the cluster nodes. Required
configuration steps are done by Heat given a specific user data config
that normally should not be changed.

## Accessing the OpenShift Cluster

### Configure DNS

OpenShift requires a two public DNS records to function fully. The first one points to
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

**NOTE**: You can skip this section if you're using the Docker image
-- it already has the `oc` binary.

You need to download the OpenShift command line client (called `oc`).
You can download and extract `openshift-origin-client-tools` from the
OpenShift release page:

https://github.com/openshift/origin/releases/latest/

Or you can now copy it from the master node:

    $ ansible -i inventory masters[0] -m fetch -a "src=/bin/oc dest=oc"

Either way, find the `oc` binary and put it in your `PATH`.


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

You can also access the OpenShift cluster with a web browser by going to:

https://master-0.openshift.example.com:8443

Note that for this to work, the OpenShift nodes must be accessible
from your computer and its DNS configuration must use the cluster's
DNS.


## Removing the OpenShift Cluster

Everything in the cluster is contained within a Heat stack. To
completely remove the cluster and all the related OpenStack resources,
run this command:

```bash
openstack stack delete --wait --yes openshift.example.com
```


## DNS configuration variables

Pay special attention to the values in the first paragraph -- these
will depend on your OpenStack environment.

Note that the provisioning playbooks update the original Neutron subnet
created with the Heat stack to point to the configured DNS servers.
So the provisioned cluster nodes will start using those natively as
default nameservers. Technically, this allows to deploy OpenShift clusters
without dnsmasq proxies.

The `openshift_openstack_clusterid` and `openshift_openstack_public_dns_domain`
will form the cluster's public DNS domain all your servers will be under. With
the default values, this will be `openshift.example.com`. For workloads, the
default subdomain is 'apps'. That subdomain can be set as well by the
`openshift_openstack_app_subdomain` variable in the inventory.

If you want to use a two sets of hostnames for public and private/prefixed DNS
records for your externally managed public DNS server, you can specify
`openshift_openstack_public_hostname_suffix` and/or
`openshift_openstack_private_hostname_suffix`. The suffixes will be added
to the nsupdate records sent to the external DNS server. Those are empty by default.

**Note** the real hostnames, Nova servers' or ansible hostnames and inventory
variables will not be updated. The deployment may be done on arbitrary named
hosts with the hostnames managed by cloud-init. Inventory hostnames will ignore
the suffixes.

The `openstack_<role name>_hostname` is a set of variables used for customising
public names of Nova servers provisioned with a given role. When such a variable stays commented,
default value (usually the role name) is used.

The `openshift_openstack_dns_nameservers` is a list of DNS servers accessible from all
the created Nova servers. These will provide the internal name resolution for
your OpenShift nodes (as well as upstream name resolution for installing
packages, etc.).

The `openshift_use_dnsmasq` controls either dnsmasq is deployed or not.
By default, dnsmasq is deployed and comes as the hosts' /etc/resolv.conf file
first nameserver entry that points to the local host instance of the dnsmasq
daemon that in turn proxies DNS requests to the authoritative DNS server.
When Network Manager is enabled for provisioned cluster nodes, which is
normally the case, you should not change the defaults and always deploy dnsmasq.

`openshift_openstack_external_nsupdate_keys` describes an external authoritative DNS server(s)
processing dynamic records updates in the public only cluster view:

    openshift_openstack_external_nsupdate_keys:
      public:
        key_secret: <some nsupdate key>
        key_algorithm: 'hmac-md5'
        key_name: 'update-key'
        server: <public DNS server IP>

Here, for the public view section, we specified another key algorithm and
optional `key_name`, which normally defaults to the cluster's DNS domain.
This just illustrates a compatibility mode with a DNS service deployed
by OpenShift on OSP10 reference architecture, and used in a mixed mode with
another external DNS server.

## Flannel networking

In order to configure the
[flannel networking](https://docs.openshift.com/container-platform/3.6/install_config/configuring_sdn.html#using-flannel),
uncomment and adjust the appropriate `inventory/group_vars/OSEv3.yml` group vars.
Note that the `osm_cluster_network_cidr` must not overlap with the default
Docker bridge subnet of 172.17.0.0/16. Or you should change the docker0 default
CIDR range otherwise. For example, by adding `--bip=192.168.2.1/24` to
`DOCKER_NETWORK_OPTIONS` located in `/etc/sysconfig/docker-network`.

Also note that the flannel network will be provisioned on a separate isolated Neutron
subnet defined from `osm_cluster_network_cidr` and having ports security disabled.
Use the `openstack_private_data_network_name` variable to define the network
name for the heat stack resource.

After the cluster deployment done, you should run an additional post installation
step for flannel and docker iptables configuration:

    ansible-playbook openshift-ansible-contrib/playbooks/provisioning/openstack/post-install.yml

## Other configuration variables

`openshift_openstack_keypair_name` is a Nova keypair - you can see your
keypairs with `openstack keypair list`. It must correspond to the
private SSH key Ansible will use to log into the created VMs. This is
`~/.ssh/id_rsa` by default, but you can use a different key by passing
`--private-key` to `ansible-playbook`.

`openshift_openstack_default_image_name` is the default name of the Glance image the
servers will use. You can see your images with `openstack image list`.
In order to set a different image for a role, uncomment the line with the
corresponding variable (e.g. `openshift_openstack_lb_image_name` for load balancer) and
set its value to another available image name. `openshift_openstack_default_image_name`
must stay defined as it is used as a default value for the rest of the roles.

`openshift_openstack_default_flavor` is the default Nova flavor the servers will use.
You can see your flavors with `openstack flavor list`.
In order to set a different flavor for a role, uncomment the line with the
corresponding variable (e.g. `openshift_openstack_lb_flavor` for load balancer) and
set its value to another available flavor. `openshift_openstack_default_flavor` must
stay defined as it is used as a default value for the rest of the roles.

`openshift_openstack_external_network_name` is the name of the Neutron network
providing external connectivity. It is often called `public`,
`external` or `ext-net`. You can see your networks with `openstack
network list`.

`openshift_openstack_private_network_name` is the name of the private Neutron network
providing admin/control access for ansible. It can be merged with other
cluster networks, there are no special requirements for networking.

The `openshift_openstack_num_masters`, `openshift_openstack_num_infra` and
`openshift_openstack_num_nodes` values specify the number of Master, Infra and
App nodes to create.

The `openshift_openstack_cluster_node_labels` defines custom labels for your openshift
cluster node groups. It currently supports app and infra node groups.
The default value of this variable sets `region: primary` to app nodes and
`region: infra` to infra nodes.
An example of setting a customised label:
```
openshift_openstack_cluster_node_labels:
  app:
    mylabel: myvalue
```

`openshift_openstack_provision_user_commands` allows users to execute
shell commands via cloud-init for all of the created Nova servers in
the Heat stack, before they are available for SSH connections.
Note that you should use custom ansible playbooks whenever
possible, like this `provision_install_custom.yml` example playbook:
```
- import_playbook: openshift-ansible/playbooks/openstack/openshift-cluster/provision.yml

- name: My custom actions
  hosts: cluster_hosts
  tasks:
  - do whatever you want here

- import_playbook: openshift-ansible/playbooks/openstack/openshift-cluster/install.yml
```
The playbook leverages a two existing provider interfaces: `provision.yml` and
`install.yml`. For some cases, like SSH keys configuration and coordinated reboots of
servers, the cloud-init runcmd directive may be a better choice though. User specified
shell commands for cloud-init need to be either strings or lists, for example:
```
- openshift_openstack_provision_user_commands:
  - set -vx
  - systemctl stop sshd # fences off ansible playbooks as we want to reboot later
  - ['echo', 'foo', '>', '/tmp/foo']
  - [ ls, /tmp/foo, '||', true ]
  - reboot # unfences ansible playbooks to continue after reboot
```

**Note** To protect Nova servers from recreating when the user-data changes via
`openshift_openstack_provision_user_commands`, the
`user_data_update_policy` parameter configured to `IGNORE` for Heat resources.

The `openshift_openstack_nodes_to_remove` allows you to specify the numerical indexes
of App nodes that should be removed; for example, ['0', '2'],

The `docker_volume_size` is the default Docker volume size the servers will use.
In order to set a different volume size for a role,
uncomment the line with the corresponding variable (e. g. `docker_master_volume_size`
for master) and change its value. `docker_volume_size` must stay defined as it is
used as a default value for some of the servers (master, infra, app node).
The rest of the roles (etcd, load balancer, dns) have their defaults hard-coded.

**Note**: If the `openshift_openstack_ephemeral_volumes` is set to `true`, the `*_volume_size` variables
will be ignored and the deployment will not create any cinder volumes.

The `openshift_openstack_flat_secgrp`, controls Neutron security groups creation for Heat
stacks. Set it to true, if you experience issues with sec group rules
quotas. It trades security for number of rules, by sharing the same set
of firewall rules for master, node, etcd and infra nodes.

The `openshift_openstack_required_packages` variable also provides a list of the additional
prerequisite packages to be installed before to deploy an OpenShift cluster.
Those are ignored though, if the `manage_packages: False`.

## Multi-master configuration

Please refer to the official documentation for the
[multi-master setup](https://docs.openshift.com/container-platform/3.6/install_config/install/advanced_install.html#multiple-masters)
and define the corresponding [inventory
variables](https://docs.openshift.com/container-platform/3.6/install_config/install/advanced_install.html#configuring-cluster-variables)
in `inventory/group_vars/OSEv3.yml`. For example, given a load balancer node
under the ansible group named `ext_lb`:

    openshift_master_cluster_hostname: "{{ groups.ext_lb.0 }}"
    openshift_master_cluster_public_hostname: "{{ groups.ext_lb.0 }}"

## Provider Network

Normally, the playbooks create a new Neutron network and subnet and attach
floating IP addresses to each node. If you have a provider network set up, this
is all unnecessary as you can just access servers that are placed in the
provider network directly.

To use a provider network, set its name in `openshift_openstack_provider_network_name` in
`inventory/group_vars/all.yml`.

If you set the provider network name, the `openshift_openstack_external_network_name` and
`openshift_openstack_private_network_name` fields will be ignored.

**NOTE**: this will not update the nodes' DNS, so running openshift-ansible
right after provisioning will fail (unless you're using an external DNS server
your provider network knows about). You must make sure your nodes are able to
resolve each other by name.

## Security notes

Configure required `*_ingress_cidr` variables to restrict public access
to provisioned servers from your laptop (a /32 notation should be used)
or your trusted network. The most important is the `openshift_openstack_node_ingress_cidr`
that restricts public access to the deployed DNS server and cluster
nodes' ephemeral ports range.

Note, the command ``curl https://api.ipify.org`` helps finding an external
IP address of your box (the ansible admin node).

There is also the `manage_packages` variable (defaults to True) you
may want to turn off in order to speed up the provisioning tasks. This may
be the case for development environments. When turned off, the servers will
be provisioned omitting the ``yum update`` command. This brings security
implications though, and is not recommended for production deployments.

## Configure the OpenShift parameters

Finally, you need to update the DNS entry in
`inventory/group_vars/OSEv3.yml` (look at
`openshift_master_default_subdomain`).

In addition, this is the place where you can customise your OpenShift
installation for example by specifying the authentication.

The full list of options is available in this sample inventory:

https://github.com/openshift/openshift-ansible/blob/master/inventory/hosts.example

Note, that in order to deploy OpenShift origin, you should update the following
variables for the `inventory/group_vars/OSEv3.yml`, `all.yml`:

    deployment_type: origin
    openshift_deployment_type: "{{ deployment_type }}"


## Setting a custom entrypoint

In order to set a custom entrypoint, update `openshift_master_cluster_public_hostname`

    openshift_master_cluster_public_hostname: api.openshift.example.com

Note than an empty hostname does not work, so if your domain is `openshift.example.com`,
you cannot set this value to simply `openshift.example.com`.


## Using Cinder-backed Persistent Volumes

You will need to set up OpenStack credentials. You can try putting this in your
`inventory/group_vars/OSEv3.yml`:

    openshift_cloudprovider_kind: openstack
    openshift_cloudprovider_openstack_auth_url: "{{ lookup('env','OS_AUTH_URL') }}"
    openshift_cloudprovider_openstack_username: "{{ lookup('env','OS_USERNAME') }}"
    openshift_cloudprovider_openstack_password: "{{ lookup('env','OS_PASSWORD') }}"
    openshift_cloudprovider_openstack_tenant_name: "{{ lookup('env','OS_PROJECT_NAME') }}"
    openshift_cloudprovider_openstack_domain_name: "{{ lookup('env','OS_USER_DOMAIN_NAME') }}"
    openshift_cloudprovider_openstack_blockstorage_version: v2

**NOTE**: you must specify the Block Storage version as v2, because OpenShift
does not support the v3 API yet and the version detection is currently not
working properly.

For more information, consult the [Configuring for OpenStack page in the OpenShift documentation][openstack-credentials].

[openstack-credentials]: https://docs.openshift.org/latest/install_config/configuring_openstack.html#install-config-configuring-openstack

**NOTE** the OpenStack integration currently requires DNS to be configured and
running and the `openshift_hostname` variable must match the Nova server name
for each node. The cluster deployment will fail without it. If you use the
provided OpenStack dynamic inventory and configure the
`openshift_openstack_dns_nameservers` Ansible variable, this will be handled
for you.

After a successful deployment, the cluster is configured for Cinder persistent
volumes.

### Validation

1. Log in and create a new project (with `oc login` and `oc new-project`)
2. Create a file called `cinder-claim.yaml` with the following contents:

```yaml
apiVersion: "v1"
kind: "PersistentVolumeClaim"
metadata:
  name: "claim1"
spec:
  accessModes:
    - "ReadWriteOnce"
  resources:
    requests:
      storage: "1Gi"
```
3. Run `oc create -f cinder-claim.yaml` to create the Persistent Volume Claim object in OpenShift
4. Run `oc describe pvc claim1` to verify that the claim was created and its Status is `Bound`
5. Run `openstack volume list`
   * A new volume called `kubernetes-dynamic-pvc-UUID` should be created
   * Its size should be `1`
   * It should not be attached to any server
6. Create a file called `mysql-pod.yaml` with the following contents:

```yaml
apiVersion: v1
kind: Pod
metadata:
  name: mysql
  labels:
    name: mysql
spec:
  containers:
    - resources:
        limits :
          cpu: 0.5
      image: openshift/mysql-55-centos7
      name: mysql
      env:
        - name: MYSQL_ROOT_PASSWORD
          value: yourpassword
        - name: MYSQL_USER
          value: wp_user
        - name: MYSQL_PASSWORD
          value: wp_pass
        - name: MYSQL_DATABASE
          value: wp_db
      ports:
        - containerPort: 3306
          name: mysql
      volumeMounts:
        - name: mysql-persistent-storage
          mountPath: /var/lib/mysql/data
  volumes:
    - name: mysql-persistent-storage
      persistentVolumeClaim:
        claimName: claim1
```

7. Run `oc create -f mysql-pod.yaml` to create the pod
8. Run `oc describe pod mysql`
   * Its events should show that the pod has successfully attached the volume above
   * It should show no errors
   * `openstack volume list` should show the volume attached to an OpenShift app node
   * NOTE: this can take several seconds
9. After a while, `oc get pod` should show the `mysql` pod as running
10. Run `oc delete pod mysql` to remove the pod
   * The Cinder volume should no longer be attached
11. Run `oc delete pvc claim1` to remove the volume claim
   * The Cinder volume should be deleted



## Creating and using a Cinder volume for the OpenShift registry

You can optionally have the playbooks create a Cinder volume and set
it up as the OpenShift hosted registry.

To do that you need specify the desired Cinder volume name and size in
Gigabytes in `inventory/group_vars/all.yml`:

    openshift_openstack_cinder_hosted_registry_name: cinder-registry
    openshift_openstack_cinder_hosted_registry_size_gb: 10

With this, the playbooks will create the volume and set up its
filesystem. If there is an existing volume of the same name, we will
use it but keep the existing data on it.

To use the volume for the registry, you must first configure it with
the OpenStack credentials by putting the following to `OSEv3.yml`:

    openshift_cloudprovider_openstack_username: "{{ lookup('env','OS_USERNAME') }}"
    openshift_cloudprovider_openstack_password: "{{ lookup('env','OS_PASSWORD') }}"
    openshift_cloudprovider_openstack_auth_url: "{{ lookup('env','OS_AUTH_URL') }}"
    openshift_cloudprovider_openstack_tenant_name: "{{ lookup('env','OS_TENANT_NAME') }}"

This will use the credentials from your shell environment. If you want
to enter them explicitly, you can. You can also use credentials
different from the provisioning ones (say for quota or access control
reasons).

**NOTE**: If you're testing this on (DevStack)[devstack], you must
explicitly set your Keystone API version to v2 (e.g.
`OS_AUTH_URL=http://10.34.37.47/identity/v2.0`) instead of the default
value provided by `openrc`. You may also encounter the following issue
with Cinder:

https://github.com/kubernetes/kubernetes/issues/50461

You can read the (OpenShift documentation on configuring
OpenStack)[openstack] for more information.

[devstack]: https://docs.openstack.org/devstack/latest/
[openstack]: https://docs.openshift.org/latest/install_config/configuring_openstack.html


Next, we need to instruct OpenShift to use the Cinder volume for its
registry. Again in `OSEv3.yml`:

    #openshift_hosted_registry_storage_kind: openstack
    #openshift_hosted_registry_storage_access_modes: ['ReadWriteOnce']
    #openshift_hosted_registry_storage_openstack_filesystem: xfs

The filesystem value here will be used in the initial formatting of
the volume.

If you're using the dynamic inventory, you must uncomment these two values as
well:

    #openshift_hosted_registry_storage_openstack_volumeID: "{{ lookup('os_cinder', openshift_openstack_cinder_hosted_registry_name).id }}"
    #openshift_hosted_registry_storage_volume_size: "{{ openshift_openstack_cinder_hosted_registry_size_gb }}Gi"

But note that they use the `os_cinder` lookup plugin we provide, so you must
tell Ansible where to find it either in `ansible.cfg` (the one we provide is
configured properly) or by exporting the
`ANSIBLE_LOOKUP_PLUGINS=openshift-ansible-contrib/lookup_plugins` environment
variable.



## Use an existing Cinder volume for the OpenShift registry

You can also use a pre-existing Cinder volume for the storage of your
OpenShift registry.

To do that, you need to have a Cinder volume. You can create one by
running:

    openstack volume create --size <volume size in gb> <volume name>

The volume needs to have a file system created before you put it to
use.

As with the automatically-created volume, you have to set up the
OpenStack credentials in `inventory/group_vars/OSEv3.yml` as well as
registry values:

    #openshift_hosted_registry_storage_kind: openstack
    #openshift_hosted_registry_storage_access_modes: ['ReadWriteOnce']
    #openshift_hosted_registry_storage_openstack_filesystem: xfs
    #openshift_hosted_registry_storage_openstack_volumeID: e0ba2d73-d2f9-4514-a3b2-a0ced507fa05
    #openshift_hosted_registry_storage_volume_size: 10Gi

Note the `openshift_hosted_registry_storage_openstack_volumeID` and
`openshift_hosted_registry_storage_volume_size` values: these need to
be added in addition to the previous variables.

The **Cinder volume ID**, **filesystem** and **volume size** variables
must correspond to the values in your volume. The volume ID must be
the **UUID** of the Cinder volume, *not its name*.

The volume can also be formatted if you configure it in
`inventory/group_vars/all.yml`:

    openshift_openstack_prepare_and_format_registry_volume: true

**NOTE:** Formatting **will destroy any data that's currently on the volume**!

You can also run the registry setup playbook directly:

   ansible-playbook -i inventory playbooks/provisioning/openstack/prepare-and-format-cinder-volume.yaml

(the provisioning phase must be completed, first)



## Using Docker on the Ansible host

If you don't want to worry about the dependencies, you can use the
[OpenStack Control Host image][control-host-image].

[control-host-image]: https://hub.docker.com/r/redhatcop/control-host-openstack/

It has all the dependencies installed, but you'll need to map your
code and credentials to it. Assuming your SSH keys live in `~/.ssh`
and everything else is in your current directory (i.e. `ansible.cfg`,
`keystonerc`, `inventory`, `openshift-ansible`,
`openshift-ansible-contrib`), this is how you run the deployment:

    sudo docker run -it -v ~/.ssh:/mnt/.ssh:Z \
        -v $PWD:/root/openshift:Z \
        -v $PWD/keystonerc:/root/.config/openstack/keystonerc.sh:Z \
        redhatcop/control-host-openstack bash

(feel free to replace `$PWD` with an actual path to your inventory and
checkouts, but note that relative paths don't work)

The first run may take a few minutes while the image is being
downloaded. After that, you'll be inside the container and you can run
the playbooks:

    cd openshift
    ansible-playbook openshift-ansible-contrib/playbooks/provisioning/openstack/provision.yaml


## Running Custom Post-Provision Actions

A custom playbook can be run like this:

```
ansible-playbook --private-key ~/.ssh/openshift -i inventory/ openshift-ansible-contrib/playbooks/provisioning/openstack/custom-actions/custom-playbook.yml
```

If you'd like to limit the run to one particular host, you can do so as follows:

```
ansible-playbook --private-key ~/.ssh/openshift -i inventory/ openshift-ansible-contrib/playbooks/provisioning/openstack/custom-actions/custom-playbook.yml -l app-node-0.openshift.example.com
```

You can also create your own custom playbook. Here are a few examples:

### Adding additional YUM repositories

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

### Attaching additional RHN pools

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

### Adding extra Docker registry URLs

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

### Adding extra CAs to the trust chain

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


## Install OpenShift

Once it succeeds, you can install openshift by running:

    ansible-playbook openshift-ansible/playbooks/deploy_cluster.yml

## Access UI

OpenShift UI may be accessed via the 1st master node FQDN, port 8443.

## Scale Deployment up/down

### Scaling up

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
