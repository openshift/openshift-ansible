# Configuration

The majority of the configuration is handled through an Ansible inventory
directory. A sample inventory can be found at
`openshift-ansible/playbooks/openstack/sample-inventory/`.

`inventory/group_vars/all.yml` is used for OpenStack configuration,
while `inventory/group_vars/OSEv3.yml` is used for OpenShift
configuration.

Environment variables may also be used.

* [OpenStack Configuration](#openstack-configuration)
* [OpenShift Configuration](#openshift-configuration)
* [OpenStack Cloud Provider Configuration](#openstack-cloud-provider-configuration)
* [OpenStack With SSL Configuration](#openstack-with-ssl-configuration)
* [Stack Name Configuration](#stack-name-configuration)
* [DNS Configuration](#dns-configuration)
* [Kuryr Networking Configuration](#kuryr-networking-configuration)
* [Provider Network Configuration](#provider-network-configuration)
* [Multi-Master Configuration](#multi-master-configuration)
* [Provider Network Configuration](#provider-network-configuration)
* [Cinder-Backed Persistent Volumes Configuration](#cinder-backed-persistent-volumes-configuration)
* [Cinder-Backed Registry Configuration](#cinder-backed-registry-configuration)
* [Scaling The OpenShift Cluster](#scaling-the-openshift-cluster)
* [Deploying At Scale](#deploying-at-scale)


## OpenStack Configuration

In `inventory/group_vars/all.yml`:

* `openshift_openstack_keypair_name` OpenStack keypair to use.
* Role Node Counts
  * `openshift_openstack_num_masters` Number of master nodes to create.
  * `openshift_openstack_num_infra` Number of infra nodes to create.
  * `openshift_openstack_num_nodes` Number of app nodes to create.
* Role Images
  * `openshift_openstack_default_image_name` OpenStack image used by all VMs, unless a particular role image name is specified.
  * `openshift_openstack_master_image_name`
  * `openshift_openstack_infra_image_name`
  * `openshift_openstack_cns_image_name`
  * `openshift_openstack_node_image_name`
  * `openshift_openstack_lb_image_name`
  * `openshift_openstack_etcd_image_name`
* Role Flavors
  * `openshift_openstack_default_flavor` OpenStack flavor used by all VMs, unless a particular role flavor name is specified.
  * `openshift_openstack_master_flavor`
  * `openshift_openstack_infra_flavor`
  * `openshift_openstack_cns_flavor`
  * `openshift_openstack_node_flavor`
  * `openshift_openstack_lb_flavor`
  * `openshift_openstack_etcd_flavor`
* Role Hostnames: used for customizing public names of Nova servers provisioned with a given role.
  * `openshift_openstack_master_hostname` Defaults to `master`.
  * `openshift_openstack_infra_hostname` Defaults to `infra-node`.
  * `openshift_openstack_cns_hostname` Defaults to `cns`.
  * `openshift_openstack_node_hostname` Defaults to `app-node`.
  * `openshift_openstack_lb_hostname` Defaults to `lb`.
  * `openshift_openstack_etcd_hostname` Defaults to `etcd`.
* `openshift_openstack_external_network_name` OpenStack network providing external connectivity.
* `openshift_openstack_provision_user_commands` Allows users to execute shell commands via cloud-init for all of the created Nova servers in the Heat stack, before they are available for SSH connections. Note that you should use [custom Ansible playbooks](./post-install.md#run-custom-post-provision-actions) whenever possible. User specified shell commands for cloud-init need to be either strings or lists:

```
- openshift_openstack_provision_user_commands:
  - set -vx
  - systemctl stop sshd # fences off ansible playbooks as we want to reboot later
  - ['echo', 'foo', '>', '/tmp/foo']
  - [ ls, /tmp/foo, '||', true ]
  - reboot # unfences ansible playbooks to continue after reboot
```

* `openshift_openstack_nodes_to_remove` The numerical indexes of app nodes that should be removed; for example, `['0', '2']`,
* Role Docker Volume Size
  * `openshift_openstack_docker_volume_size` Default Docker volume size used by all VMs, unless a particular role Docker volume size is specified. If `openshift_openstack_ephemeral_volumes` is set to `true`, the `*_volume_size` variables will be ignored and the deployment will not create any cinder volumes.
  * `openshift_openstack_docker_master_volume_size`
  * `openshift_openstack_docker_infra_volume_size`
  * `openshift_openstack_docker_cns_volume_size`
  * `openshift_openstack_docker_node_volume_size`
  * `openshift_openstack_docker_etcd_volume_size`
  * `openshift_openstack_docker_lb_volume_size`
* `openshift_openstack_flat_secgrp` Set to True if you experience issues with sec group rules quotas. It trades security for number of rules, by sharing the same set of firewall rules for master, node, etcd and infra nodes.
* `openshift_openstack_required_packages` List of additional prerequisite packages to be installed before deploying an OpenShift cluster.
* `openshift_openstack_heat_template_version` Defaults to `pike`


## OpenShift Configuration

In `inventory/group_vars/OSEv3.yml`:

* `openshift_disable_check` List of checks to disable.
* `openshift_master_cluster_public_hostname` Custom entrypoint; for example, `api.openshift.example.com`. Note than an empty hostname does not work, so if your domain is `openshift.example.com` you cannot set this value to simply `openshift.example.com`.
* `openshift_deployment_type` Version of OpenShift to deploy; for example, `origin` or `openshift-enterprise`
* `openshift_master_default_subdomain`

Additional options can be found in this sample inventory:

https://github.com/openshift/openshift-ansible/blob/master/inventory/hosts.example


## OpenStack Cloud Provider Configuration

Some features require you to configure the OpenStack cloud provider. For example, in
`inventory/group_vars/OSEv3.yml`:

* `openshift_cloudprovider_kind`: openstack
* `openshift_cloudprovider_openstack_auth_url`: "{{ lookup('env','OS_AUTH_URL') }}"
* `openshift_cloudprovider_openstack_username`: "{{ lookup('env','OS_USERNAME') }}"
* `openshift_cloudprovider_openstack_password`: "{{ lookup('env','OS_PASSWORD') }}"
* `openshift_cloudprovider_openstack_tenant_name`: "{{ lookup('env','OS_PROJECT_NAME') }}"
* `openshift_cloudprovider_openstack_domain_name`: "{{ lookup('env','OS_USER_DOMAIN_NAME') }}"

The full range of openshift-ansible OpenStack cloud provider options can be found at:

https://github.com/openshift/openshift-ansible/blob/master/roles/openshift_cloud_provider/templates/openstack.conf.j2

For more information, consult the [Configuring for OpenStack page in the OpenShift documentation][openstack-credentials].

[openstack-credentials]: https://docs.openshift.org/latest/install_config/configuring_openstack.html#install-config-configuring-openstack

If you would like to use additional parameters, create a custom cloud provider
configuration file locally and specify it in `inventory/group_vars/OSEv3.yml`:

* `openshift_cloudprovider_openstack_conf_file` Path to local openstack.conf


## OpenStack With SSL Configuration

In order to configure your OpenShift cluster to work properly with OpenStack with
SSL-endpoints, add the following to `inventory/group_vars/OSEv3.yml`:

```
openshift_certificates_redeploy: true
openshift_additional_ca: /path/to/ca.crt.pem
kuryr_openstack_ca: /path/to/ca.crt.pem (optional)
openshift_cloudprovider_openstack_ca_file: |
  -----BEGIN CERTIFICATE-----
  CONTENTS OF OPENSTACK SSL CERTIFICATE
  -----END CERTIFICATE-----
```

## Stack Name Configuration

By default the Heat stack created by OpenStack for the OpenShift cluster will be
named `openshift-cluster`. If you would like to use a different name then you
must set the `OPENSHIFT_CLUSTER` environment variable before running the playbooks:

```
$ export OPENSHIFT_CLUSTER=openshift.example.com
```

If you use a non-default stack name and run the openshift-ansible playbooks to update
your deployment, you must set `OPENSHIFT_CLUSTER` to your stack name to avoid errors.


## DNS Configuration

For its installation, OpenShift requires that the nodes can resolve each other
by their hostnames. Specifically, the hostname must resolve to the private
(i.e. nonfloating) IP address.

Most OpenStack deployments do not support this out of the box. If you have a
control over your OpenStack, you can set this up in the [OpenStack Internal
DNS](#openstack-internal-dns) section.

Otherwise, you need an external DNS server.

While we do not create a DNS for you, if it supports nsupdate (RFC
2136[nsupdate-rfc]), we can populate it with the cluster records
automatically.

[nsupdate-rfc]: https://www.ietf.org/rfc/rfc2136.txt

### OpenShift Cluster Domain

To set up the domain name of your OpenShift cluster, set these
parameters in `inventory/group_vars/all.yml`:

* `openshift_openstack_clusterid` Defaults to `openshift`
* `openshift_openstack_public_dns_domain` Defaults to `example.com`

Together, they form the cluster's public DNS domain that all the
servers will be under; by default this domain will be
`openshift.example.com`.

They're split so you can deploy multiple clusters under the same
domain with a single inventory change: e.g. `testing.example.com` and
`production.example.com`.

You will also want to put the IP addresses of your DNS server(s) in
the `openshift_openstack_dns_nameservers` array in the same file.

This will configure the Neutron subnet with all the OpenShift nodes to forward
to these DNS servers. Which means that any server running in that subnet will
use the DNS automatically, without any extra configuration.


### OpenStack Internal DNS

This is the preferred way to handle internal node name resolution.

OpenStack Neutron is capable of resolving its servers by name, but it needs to
be configured to do so. This requires operator access to the OpenStack servers
and services.


#### Configure Neutron Internal DNS

In `/etc/neutron/neutron.conf`, set the `dns_domain` option. For example:

    dns_domain = internal.

Note the trailing dot. This can be a domain name or any string and it does
not have to be externally resolvable. Values such as `openshift.cool.`,
`example.com.` or `openstack-internal.` are all fine.

It must not be `openshiftlocal.` however. That is the default value and it does
not provide the behaviour we need.

Next, in `/etc/neutron/plugins/ml2/ml2_conf.ini`, add the `dns_domain_ports`
extension driver:

    extension_drivers=dns_domain_ports

If you already have other drivers set, just add it at the end, separated by a
coma. E.g.:

    extension_drivers=port_security,dns_domain_ports

Finally, restart the `neutron-server` service:

    systemctl restart neutron-server

(or `systemctl restart 'devstack@q-svc'` in DevStack)


To verify that it works, you should create two servers, SSH into one of them
and ping the other one by name. For example

    $ openstack server create .... --network private test1
    $ openstack server create .... --network private test2
    $ openstack floating ip create external
    $ openstack server add floating ip test1 <floating ip>
    $ ssh centos@<floating ip>
      $ ping test2

If the ping succeeds, everything is set up correctly.

For more information, read the relevant OpenStack documentation:

https://docs.openstack.org/neutron/latest/admin/config-dns-int.html


#### Configure Playbooks To Use Internal DNS

Since the internal DNS does not use the domain name suffix our OpenShift
cluster will work with, we must make sure that our Nodes' hostnames
do not have it either. Nor should they use any other internal DNS server.

Put this in your `inventory/group_vars/all.yml`:

```yaml
openshift_openstack_fqdn_nodes: false
openshift_openstack_dns_nameservers: []
```

The nodes will now be called `master-0` instead of
`master-0.openshift.example.com`. Neutron's DNS resolution requires these short
hostnames.

If you were using a private DNS before, you'll also want to remove the
`private` section of `openshift_openstack_external_nsupdate_keys` (the `public`
one is okay). The internal name resolution is handled by Neutron so the DNS and
its private records are no longer necessary.

If you're setting `openshift_master_cluster_hostname` to a master node, it must
be updated accordingly, too (e.g. `openshift_master_cluster_hostname:
master-0`).

And finally, run the `provision_install.yml` playbooks as you normally would.


### Adding the DNS Records Automatically

If you don't have operator access to your OpenStack, it may still be configured
to provide server name resolution anyway. Try running the validation steps from
the [OpenStack Internal DNS](#openstack-internal-dns) section. If ping fails,
you will need to use an external DNS server.

If your DNS supports nsupdate, you can set up the
`openshift_openstack_external_nsupdate_keys` variable and all the necessary DNS
records will be added during the provisioning phase (after the OpenShift nodes
are created, but before we install anything on them).

Add this to your `inventory/group_vars/all.yml`:

```
    openshift_openstack_external_nsupdate_keys:
      private:
        key_secret: <some nsupdate key>
        key_algorithm: 'hmac-md5'
        key_name: 'update-key'
        server: <private DNS server IP>
```

Make sure that all four values (key secret, algorithm, key name and
the DNS IP address) are correct.

This will create the records for the internal OpenShift communication.
If you also want public records for external access, add another
section called `public` with the same structure.

If you want to use the same DNS server for both public and private
records, you must set at least one of:

* `openshift_openstack_public_hostname_suffix` Empty by default.
* `openshift_openstack_private_hostname_suffix` Empty by default.

Otherwise the private records will be overwritten by the public ones.

For example by leaving the *private* suffix empty and setting the *public* one
to:

```
openshift_openstack_public_hostname_suffix: -public
```

The internal access to the first master node would be available with:
`master-0.openshift.example.com`, while the public access using the floating IP
address would be under `master-0-public.openshift.example.com`.

Note that these suffixes are only applied to the OpenShift Node names
as they appear in the DNS. They will not affect the actual hostnames.

It is recommended that you use two separate servers for the private
and public access instead.

If your nsupdate zone differs from the full OpenShift DNS name (e.g.
your DNS' zone is "example.com" but you want your cluster to be at
"openshift.example.com"), you can specify the zone in this parameter:

* `openshift_openstack_nsupdate_zone: example.com`

If left out, it will be equal to the OpenShift cluster DNS.

Don't forget to put your the internal (private) DNS servers to the
`openshift_openstack_dns_nameservers` array.


### Custom DNS Records Configuration

If you're unable (or do not want) to use nsupdate, you will have to
create your DNS records out-of-band.

To do that, you will have to split the deployment into three phases:

1. Provision (creates the OpenShift servers)
2. Create DNS records (this is your responsibility)
3. Installation (installs OpenShift on the servers)

To do this, run the `provision.yml` and `install.yml` playbooks
instead of the all-in-one `provision_install.yml` and add your DNS
records between the runs.

You still need to set the `openshift_openstack_dns_nameservers` with
your (private/internal) DNS servers in `inventory/group_vars/all.yml`.

Next, you need to create a DNS record for every OpenShift node that
was created. This record must point to the node's **private** IP
address (not the floating IP).

You can see the server names and their private floating IP addresses
by running `openstack server list`.

For example with the following output:

```
$ openstack server list
+--------------------------------------+--------------------------------------+---------+----------------------------------------------------------------------------+---------+-----------+
| ID                                   | Name                                 | Status  | Networks                                                                   | Image   | Flavor    |
+--------------------------------------+--------------------------------------+---------+----------------------------------------------------------------------------+---------+-----------+
| 8445bd74-aaf1-4c54-b6fe-e98efa6e47de | master-0.openshift.example.com     | ACTIVE  | openshift-ansible-openshift.example.com-net=192.168.99.10, 10.40.128.136 | centos7 | m1.medium |
| 635f0a24-bde7-488d-aa0d-c31e0a01e7c4 | infra-node-0.openshift.example.com | ACTIVE  | openshift-ansible-openshift.example.com-net=192.168.99.4, 10.40.128.130  | centos7 | m1.medium |
| 04657a99-29b1-48c8-8979-3c88ee1c1615 | app-node-0.openshift.example.com   | ACTIVE  | openshift-ansible-openshift.example.com-net=192.168.99.6, 10.40.128.132  | centos7 | m1.medium |
+--------------------------------------+--------------------------------------+---------+----------------------------------------------------------------------------+---------+-----------+
```

You will need to create these A records:

```
master-0.openshift.cool.       192.168.99.10
infra-node-0.openshift.cool.   192.168.99.4
app-node-0.openshift.cool.     192.168.99.16
```

For the public access, you'll need to create 2 records: one for the
API access and the other for the OpenShift apps running on the
cluster.

```
console.openshift.cool.    10.40.128.137
*.apps.openshift.cool.     10.40.128.129
```

These must point to the publicly-accessible IP addresses of your
master and infra nodes or preferably to the load balancers.


## Kuryr Networking Configuration

Kuryr is an SDN that uses OpenStack Neutron. This prevents the double overlay
overhead one would get when running OpenShift on OpenStack using the default
OpenShift SDN.

https://docs.openstack.org/kuryr-kubernetes/latest/readme.html

### OpenStack Requirements

Kuryr has a few additional requirements on the underlying OpenStack deployment:

* The Trunk Ports extension must be enabled:
  * https://docs.openstack.org/neutron/pike/admin/config-trunking.html
  * Make sure to restart `neutron-server` after you change the configuration
* Neutron must use the Open vSwitch firewall driver:
  * https://docs.openstack.org/neutron/pike/admin/config-ovsfwdriver.html
  * Make sure to restart `neutron-openvswitch-agent` after the config change
* A Load Balancer as a Service (implementing LBaaS v2 API) must be available
  * Octavia is the only supported solution right now
  * You could try the native Neutron LBaaSv2 but it is deprecated and buggy

We recommend you use the Queens or newer release of OpenStack.


### Necessary Kuryr Options

This is the minimum you need to set (in `group_vars/all.yml`):

```yaml
openshift_use_kuryr: true
openshift_use_openshift_sdn: false
os_sdn_network_plugin_name: cni
openshift_node_proxy_mode: userspace
use_trunk_ports: true

openshift_master_open_ports:
- service: dns tcp
  port: 53/tcp
- service: dns udp
  port: 53/udp
openshift_node_open_ports:
- service: dns tcp
  port: 53/tcp
- service: dns udp
  port: 53/udp

kuryr_openstack_public_net_id: <public/external net UUID>
```

The `kuryr_openstack_public_net_id` value must be set to the UUID of the
public net in your OpenStack. In other words, the net with the Floating
IP range defined. It corresponds to the public network, which is often called
`public`, `external` or `ext-net`.

Additionally, if the public net has different subnet, you can specify the
specific one with `kuryr_openstack_public_subnet_id`, whose value must be set
to the UUID of the public subnet in your OpenStack.

**NOTE**: A lot of OpenStack deployments do not make the public subnet
accessible to regular users.

Finally, you *must* set up an OpenStack cloud provider as specified in
 [OpenStack Cloud Provider Configuration](#openstack-cloud-provider-configuration).

### Port pooling

It is possible to pre-create Neutron ports for later use. This means that
several ports (each port will be attached to an OpenShift pod) would be created
at once. This will speed up individual pod creation at the cost of having a few
extra ports that are not currently in use.

For more information on the Kuryr port pools, check out the Kuryr
documentation:

https://docs.openstack.org/kuryr-kubernetes/latest/installation/ports-pool.html

You can control the port pooling characteristics with these options:

```yaml
kuryr_openstack_pool_max: 0
kuryr_openstack_pool_min: 1
kuryr_openstack_pool_batch: 5
kuryr_openstack_pool_update_frequency: 20
`openshift_kuryr_precreate_subports: 5`
```

Note in the last variable you specify the number of subports that will
be created per trunk port, i.e., per pool.

You need to set the pool driver you want to use, depending on the target
environment, i.e., neutron for baremetal deployments or nested for deployments
on top of VMs:

```yaml
kuryr_openstack_pool_driver: neutron
kuryr_openstack_pool_driver: nested
```

And to disable this feature, you must set:

```yaml
kuryr_openstack_pool_driver: noop
```

On the other hand, there is a multi driver support to enable hybrid
deployments with different pools drivers. In order to enable the kuryr
`multi-pool` driver support, we need to also tag the nodes with their
corresponding `pod_vif` labels so that the right kuryr pool driver is used
for each VM/node.

To do that, set this in `inventory/group_vars/OSEv3.yml`:

```yaml
kuryr_openstack_pool_driver: multi

openshift_node_groups:
  - name: node-config-master
    labels:
      - 'node-role.kubernetes.io/master=true'
      - 'pod_vif=nested-vlan'
    edits: []
  - name: node-config-infra
    labels:
      - 'node-role.kubernetes.io/infra=true'
      - 'pod_vif=nested-vlan'
    edits: []
  - name: node-config-compute
    labels:
      - 'node-role.kubernetes.io/compute=true'
      - 'pod_vif=nested-vlan'
    edits: []
```


### Kuryr Controller and CNI healthchecks probes

By default kuryr controller and cni pods are deployed with readiness and
liveness probes enabled. To disable them you can just uncomment:

```yaml
enable_kuryr_controller_probes: True
enable_kuryr_cni_probes: True
```


## API and Router Load Balancing

A production deployment should contain more then one master and infra node and
have a load balancer in front of them.

The playbooks will not create any load balancer by default. Even if you do
request multiple masters.

You can opt into that if you want though. There are two options: a VM-based
load balancer and OpenStack's Load Balancer as a Service.

### Load Balancer as a Service

If your OpenStack supports Load Balancer as a Service (LBaaS) provided by the
Octavia project, our playbooks can set it up automatically.

Put this in your `inventory/group_vars/all.yml`:

    openshift_openstack_use_lbaas_load_balancer: true

This will create two load balancers: one for the API and UI console and the
other for the OpenShift router. Each will have its own public IP address.

This playbook defaults to using OpenStack Octavia as its LBaaSv2 provider:

    openshift_openstack_lbaasv2_provider: Octavia

If your cloud uses the deprecated Neutron LBaaSv2 provider set:

    openshift_openstack_lbaasv2_provider: "Neutron::LBaaS"

### VM-based Load Balancer

If you can't use OpenStack's LBaaS, we can create and configure a virtual
machine running HAProxy to serve as one.

Put this in your `inventory/group_vars/all.yml`:

    openshift_openstack_use_vm_load_balancer: true

**WARNING** this VM will only handle the API and UI requests, *not* the
OpenShift routes.

That means, if you have more than one infra node, you will have to balance them
externally. It is not recommended to use this option in production.

### No Load Balancer

If you specify neither `openshift_openstack_use_lbaas_load_balancer` nor
`openshift_openstack_use_vm_load_balancer`, the resulting OpenShift cluster
will have no load balancing configured out of the box.

This is regardless of how many master or infra nodes you create.

In this mode, you are expected to configure and maintain a load balancer
yourself.

However, the cluster is usable without a load balancer as well. To talk to the
API or UI, connect to any of the master nodes. For the OpenShift routes, use
any of the infra nodes.

### Public Cluster Endpoints

In either of these cases (LBaaS, VM HAProxy, no LB) the public addresses to
access the cluster's API and router will be printed out at the end of the
playbook.

If you want to get them out explicitly, run the following playbook with the
same arguments (private key, inventories, etc.) as your provision/install ones:

    playbooks/openstack/inventory.py openshift-ansible/playbooks/openstack/openshift-cluster/cluster-info.yml

These addresses will depend on the load balancing solution. For LBaaS, they'll
be the the floating IPs of the load balancers. In the VM-based solution,
the API address will be the public IP of the load balancer VM and the router IP
will be the address of the first infra node that was created. If no load
balancer is selected, the API will be the address of the first master node and
the router will be the address of the first infra node.

This means that regardless of the load balancing solution, you can use these
two entries to provide access to your cluster.


## Provider Network Configuration

Normally, the playbooks create a new Neutron network and subnet and attach
floating IP addresses to each node. If you have a provider network set up, this
is all unnecessary as you can just access servers that are placed in the
provider network directly.

Note that this will not update the nodes' DNS, so running openshift-ansible
right after provisioning will fail (unless you're using an external DNS server
your provider network knows about). You must make sure your nodes are able to
resolve each other by name.

In `inventory/group_vars/all.yml`:

* `openshift_openstack_provider_network_name` Provider network name. Setting this will cause the `openshift_openstack_external_network_name` and `openshift_openstack_private_network_name` parameters to be ignored.


## Cinder-Backed Persistent Volumes Configuration

In addition to [setting up an OpenStack cloud provider](#openstack-cloud-provider-configuration),
you must set the following in `inventory/group_vars/OSEv3.yml`:

* `openshift_cloudprovider_openstack_blockstorage_version`: v2

The Block Storage version must be set to `v2`, because OpenShift does not support
the v3 API yet and the version detection currently does not work.

After a successful deployment, the cluster will be configured for Cinder persistent
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


## Cinder-Backed Registry Configuration

You can use a pre-existing Cinder volume for the storage of your
OpenShift registry. To do that, you need to have a Cinder volume.
You can create one by running:

```
openstack volume create --size <volume size in gb> <volume name>
```

Alternatively, the playbooks can create the volume created automatically if you
specify its name and size.

In either case, you have to [set up an OpenStack cloud provider](#openstack-cloud-provider-configuration),
and then set the following in `inventory/group_vars/OSEv3.yml`:

* `openshift_hosted_registry_storage_kind`: openstack
* `openshift_hosted_registry_storage_access_modes`: ['ReadWriteOnce']
* `openshift_hosted_registry_storage_openstack_filesystem`: xfs
* `openshift_hosted_registry_storage_volume_size`: 10Gi

For a volume *you created*, you must also specify its **UUID** (it must be
the UUID, not the volume's name):

```
openshift_hosted_registry_storage_openstack_volumeID: e0ba2d73-d2f9-4514-a3b2-a0ced507fa05
```

If you want the volume *created automatically*, set the desired name instead:

```
openshift_hosted_registry_storage_volume_name: registry
```

The volume will be formatted automaticaly and it will be mounted to one of the
infra nodes when the registry pod gets started.


## Scaling The OpenShift Cluster

Adding more nodes to the cluster is a three-step process: we need to create the
new nodes, mark them for scale up and then run the appropriate playbook.

Note that the scaling playbooks are different from the installation ones. If
you just change the number of nodes in your inventory and re-run
`provision_install.yml`, the playbooks will fail.

### Scaling the Compute and Infra Nodes

#### 1. Adding Extra Nodes

Edit your `inventory/group_vars/all.yml` and set the new node total in
`openshift_openstack_num_nodes`.

For example, if your cluster has currently 3 masters, 2 infra and 5 app nodes
and you want to add another 3 compute nodes, `all.yml` should contain this:

```
openshift_openstack_num_masters: 3
openshift_openstack_num_infra: 2
openshift_openstack_num_nodes: 8  # 5 existing and 3 new
```

**NOTE**: scaling the infra nodes is exactly the same. Just update the
`openshift_openstack_num_infra` var instead.

Then run the `provision.yml` playbook only (*do not run*
`provision_install.yml` -- it can mess up your cluster!).

```
$ ansible-playbook --user openshift \
  -i openshift-ansible/playbooks/openstack/inventory.py \
  -i inventory \
  openshift-ansible/playbooks/openstack/openshift-cluster/provision.yml
```

This will create the new nodes while leaving everything else as is.


#### 2. Marking The Nodes For Scaleup

You can see all nodes (old as well as new) by running:

```
openstack server list
```

Note the names of the newly created nodes.

Then create a new text file called `new-nodes` with the following contents:

```
[new_nodes]
app-node-5.openshift.example.com
app-node-6.openshift.example.com
app-node-7.openshift.example.com

[OSEv3:children]
new_nodes
```

That is, an ini group section called `new_nodes` and the name of every new node
on its own line. If you're scaling the infra nodes, they should go into the
`new_nodes` section as well.

You must also run the `configure-new-nodes.yml` playbook to run a few
OpenStack-specific configurations. Don't forget to pass the `new-nodes` file
in.

```
$ ansible-playbook --user openshift \
  -i openshift-ansible/playbooks/openstack/inventory.py \
  -i new-nodes \
  -i inventory \
  openshift-ansible/playbooks/openstack/openshift-cluster/configure-new-nodes.yml
```

#### 3. Adding The Nodes To OpenShift

The final step is running the `scaleup.yml` playbook and passing in the
`new-nodes` file:

```
$ ansible-playbook --user openshift \
  -i openshift-ansible/playbooks/openstack/inventory.py \
  -i new-nodes \
  -i inventory \
  openshift-ansible/playbooks/openshift-node/scaleup.yml
```

After that, your OpenShift cluster will be configured with the extra nodes. Be
sure to **remove the `-i new-nodes` parameter from any subsequent Ansible
runs** as these "new nodes" are now "regular nodes".

For any subsequent scaling operations, you will have to update the `new-nodes`
file. The `new_nodes` group should only contain nodes that were not deployed.
So you would remove the previously added nodes and put in the new ones.

For more information on scaling, please visit the [OpenShift Admin
Guide][admin-guide].

[admin-guide]: https://docs.openshift.org/latest/admin_guide/manage_nodes.html#adding-cluster-hosts_manage-nodes


#### 4. Updating The Registry and Router Replicas

If you have added new infra nodes, the extra `docker-registry` and `router`
pods may not have been created automatically. E.g. if you started with a single
infra node and then scaled it to three, you might still only see a single
registry and router.

In that case, you can scale the pods them by running the following as the
OpenShift admin:

```
oc scale --replicas=<count> dc/docker-registry
oc scale --replicas=<count> dc/router
```

Where `<count>` is the number of the pods you want (i.e. the number of your
infra nodes).


## Deploying At Scale

By default, heat stack outputs are resolved.  This may cause
problems in large scale deployments.  Querying heat stack can take
a long time and eventually time out.  The following setting in
`inventory/group_vars/all.yml` is recommended to prevent the timeouts:

* `openshift_openstack_resolve_heat_outputs`: False
