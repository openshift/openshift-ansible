## OpenStack Kuryr

Install Kuryr CNI components (kuryr-controller, kuryr-cni) on Master and worker
nodes. Kuryr uses OpenStack Networking service (Neutron) to provide network for
pods. This allows to have interconnectivity between pods and OpenStack VMs.

## Requirements

* Ansible 2.2+
* Centos/ RHEL 7.3+

## Current Kuryr restrictions when used with OpenShift

* Openshift Origin only
* OpenShift on OpenStack Newton or newer (only with Trunk ports)

## Key Ansible inventory Kuryr master configuration parameters

* ``openshift_use_kuryr=True``
* ``openshift_use_openshift_sdn=False``
* ``openshift_sdn_network_plugin_name='cni'``
* ``kuryr_cni_link_interface=eth0``
* ``kuryr_openstack_auth_url=keystone_url``
* ``kuryr_openstack_user_domain_name=Default``
* ``kuryr_openstack_user_project_name=Default``
* ``kuryr_openstack_project_id=project_uuid``
* ``kuryr_openstack_username=kuryr``
* ``kuryr_openstack_password=kuryr_pass``
* ``kuryr_openstack_pod_sg_id=pod_security_group_uuid``
* ``kuryr_openstack_pod_subnet_id=pod_subnet_uuid``
* ``kuryr_openstack_pod_service_id=service_subnet_uuid``
* ``kuryr_openstack_pod_project_id=pod_project_uuid``
* ``kuryr_openstack_worker_nodes_subnet_id=worker_nodes_subnet_uuid``
* ``kuryr_openstack_enable_pools=True``
* ``kuryr_openstack_pool_max=0``
* ``kuryr_openstack_pool_min=1``
* ``kuryr_openstack_pool_batch=5``
* ``kuryr_openstack_pool_update_frequency=20``

## Kuryr resources

* [Kuryr documentation](https://docs.openstack.org/kuryr-kubernetes/latest/)
* [Installing Kuryr containerized](https://docs.openstack.org/kuryr-kubernetes/latest/installation/containerized.html)
