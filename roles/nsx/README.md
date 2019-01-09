# NSX-T

Configure Openshift NSX-T integration.

## Requirements

* Ansible 2.4+

The Openshift VMs need to be hosted on NSX-T prepared ESXi or KVM hypervisors.
Other than the management vNic the openshift VMs need to have second vNic
for POD data traffic. This second vNic need to have the following tags
for every VM in NSX:
```
{'ncp/node_name':  '<node_name>'}
{'ncp/cluster': '<cluster_name>'}
```
Currently the nsx container docker image is not publically available.
While we fix this you need the image nsx-ncp in a local private registry
or do the following:
* `ansible-playbook [-i /path/to/inventory] playbooks/prerequisites.yml`
On all nodes:
* `docker load -i nsx-ncp-rhel-2.3.2.11627441.tar`
* `docker image tag registry.local/2.3.2.11627441/nsx-ncp-rhel nsx-ncp`
* `ansible-playbook [-i /path/to/inventory] playbooks/deploy_cluster.yml`

## Installation

To install, set the following inventory configuration parameters:

* `openshift_use_nsx=True`
* `openshift_use_openshift_sdn=False`
* `os_sdn_network_plugin_name='cni'`

NSX specific parameters:

* `nsx_openshift_cluster_name='ocp-cluster1'`
(Required) NSX supports multiple Openshift/K8S clusters connected to the same 
NSX Manager, so we mandate to provide cluster name in order to recognise.
* `nsx_api_managers='10.10.10.10'`
(Required) IP address of NSX Manager. If cluster of managers
three ip addresses separated by comma.
* `nsx_tier0_router='MyT0Router'`
(Required) Name or uuid of the precreated T0 router
where the project's T1 routers will be connected to
* `nsx_overlay_transport_zone='my_overlay_tz'`
(Required) Name or uuid of the overlay transport zone
that will be used to create logical switches. 
* `nsx_container_ip_block='ip_block_for_my_ocp_cluster'`
(Required) Name or uuid of an ip block configured on NSX. There will be a subnet
per project out of this ip block. Those networks will be behind SNAT and not routable.
* `nsx_ovs_uplink_port='ens224'`
(Required) If in HOSTVM mode. NSX needs second vNIC for POD networking on the OCP nodes,
different then management vNIC. It is highly recomended both vNICs to be connected to
NSX-T Logical Switches. The second (non-management) vNIC needs to be supplied here.
For Baremetal this can be ignored.
* `nsx_cni_url='http://myserver/nsx-cni.rpm'`
(Required) Temporary requirement until NCP can bootstrap the nodes.
We need to place nsx-cni in an http server.
* `nsx_ovs_url='http://myserver/openvswitch.rpm'`
* `nsx_kmod_ovs_url='http://myserver/kmod-openvswitch.rpm'`
(Required) Temporary parameters until NCP can bootstrap the nodes.
Can be ignored in baremetal setup.

* `nsx_node_type='HOSTVM'`
(Optional) Defaults to HOSTVM. Set to BAREMETAL if Openshift is not
running in VMs.
* `nsx_k8s_api_ip=192.168.10.10`
(Optional) If set, NCP will talk to this ip, otherwise to kubernetes service ip.
* `nsx_k8s_api_port=192.168.10.10`
(Optional) Default to 443 for k8s service. Set to 8443 if you use it in combination
with nsx_k8s_api_ip to specify master node ip.
* `nsx_insecure_ssl=true`
(Optional) Default is true as NSX Manager comes with untrusted certificate.
If you have changed the certificate with a trusted one you can set it to false
* `nsx_api_user='admin'`
* `nsx_api_password='super_secret_password'`
* `nsx_subnet_prefix=24`
(Optional) Defaults to /24. This is the subnet size that will be dedicated per 
Openshift Project. If number of PODs exceed the subnet size a new Logical Switch
with the same subnet size will be added to the project.
* `nsx_use_loadbalancer=true`
(Optional) Defaults to true. Set to false if you don't want to use 
NSX-T Loadbalancer for Route and Service type LoadBalancer
* `nsx_lb_service_size='SMALL'`
(Optional) Defaults to SMALL. Depending on the Edge size MEDIUM/LARGE 
can also be possible
* `nsx_no_snat_ip_block='router_ip_block_for_my_ocp_cluster'`
(Optional) If ncp/no_snat=true annotation is applied on
a project/namespace the subnet will be taken from this ip block
and there will be no SNAT for it. It is expected to be routable
* `nsx_external_ip_pool='external_pool_for_snat'`
(Requred) Precreated ip pool for SNAT and LB if nsx_external_ip_pool_lb is not defined.
* `nsx_external_ip_pool_lb='my_ip_pool_for_lb'`
(Optional) Set this if you want distinct ip pool for Router and SvcTypeLB.
* `nsx_top_fw_section='top_section'`
(Optional) K8s network policy rules will be translated 
to NSX dFW and placed below this precreated section
* `nsx_bottom_fw_section='bottom_section'`
(Optional) K8s network policy rules will be translated 
to NSX dFW and placed before this precreated section
* `nsx_api_cert='/path/to/cert/nsx.crt'`
* `nsx_api_private_key='/path/to/key/nsx.key`
(Optional) If set, nsx_api_user and nsx_api_password will be ignored.
The certificate must be uploaded to NSX and a Principal Identity user
authenticating with this cert must be manually created.
* `nsx_lb_default_cert='/path/to/cert/nsx.crt'`
* `nsx_lb_default_key='/path/to/key/nsx.key`
(Optional) NSX-T LoadBalancer requires a default certificate in order
to be able to crate SNIs for TLS based Routes. This certificate will be presented
only if there is no Route configured. If not provided self-signed certificate
will be generated.

## Example host file

```
[OSEv3:children]
masters
nodes
etcd

[OSEv3:vars]
ansible_ssh_user=root
openshift_deployment_type=origin

openshift_master_identity_providers=[{'name': 'htpasswd_auth', 'login': 'true', 'challenge': 'true', 'kind': 'HTPasswdPasswordIdentityProvider'}]
openshift_master_htpasswd_users={'yasen' : 'password'}

openshift_master_default_subdomain=demo.corp.local
openshift_use_nsx=true
os_sdn_network_plugin_name=cni
openshift_use_openshift_sdn=false
openshift_node_sdn_mtu=1500

# NSX specific configuration
nsx_openshift_cluster_name='ocp-cluster1'
nsx_api_managers='192.168.110.201'
nsx_api_user='admin'
nsx_api_password='VMware1!'
nsx_tier0_router='DefaultT0Router'
nsx_overlay_transport_zone='overlay-tz'
nsx_container_ip_block='ocp-pod-networking'
nsx_no_snat_ip_block='ocp-nonat-pod-networking'
nsx_external_ip_pool='ocp-external'
nsx_top_fw_section='openshift-top'
nsx_bottom_fw_section='openshift-bottom'
nsx_ovs_uplink_port='ens224'
nsx_cni_url='http://1.1.1.1/nsx-cni-2.3.2.x86_64.rpm'
nsx_ovs_url='http://1.1.1.1/openvswitch-2.9.1.rhel75-1.x86_64.rpm'
nsx_kmod_ovs_url='http://1.1.1.1/kmod-openvswitch-2.9.1.rhel75-1.el7.x86_64.rpm'

[masters]
ocp-master.corp.local

[etcd]
ocp-master.corp.local

[nodes]
ocp-master.corp.local ansible_ssh_host=10.1.0.10 openshift_node_group_name='node-config-master'
ocp-node1.corp.local ansible_ssh_host=10.1.0.11 openshift_node_group_name='node-config-infra'
ocp-node2.corp.local ansible_ssh_host=10.1.0.12 openshift_node_group_name='node-config-infra'
ocp-node3.corp.local ansible_ssh_host=10.1.0.13 openshift_node_group_name='node-config-compute'
ocp-node4.corp.local ansible_ssh_host=10.1.0.14 openshift_node_group_name='node-config-compute'

```

## Upgrading
Upgrading NSX-T is an independent process. Please follow VMware documentation.

### Contact Information

Author: Yasen Simeonov <simeonovy@vmware.com>
