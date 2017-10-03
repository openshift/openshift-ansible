# Contrail SDN

Contrail, based on OpenContrail, is a truly open, multi-cloud network virtualization and policy management platform. Contrail / OpenContrail is integrated with various orchestration systems such as Kubernetes, OpenShift, OpenStack and Mesos, and provides different isolation modes for virtual machines, containers/pods and bare metal workloads

## Installation

To install Contrail SDN with OpenShift, set the following inventory configuration parameters:

* `openshift_use_contrail=True`
* `openshift_use_openshift_sdn=False`
* `os_sdn_network_plugin_name='cni'`
* `os_release=redhat7`
* `contrail_version=4.0.1.0-44`
* `vrouter_physical_interface=eno1`
* `contrail_docker_images_path=/root`
* `analyticsdb_min_diskgb=25`
* `configdb_min_diskgb=25`

### Contact Information

Author: Savithru Lokanath <slokanath@juniper.net>
