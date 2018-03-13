# Contrail SDN

[Contrail Networking](https://www.juniper.net/us/en/products-services/sdn/contrail/contrail-networking/), based on [OpenContrail](http://www.opencontrail.org/) project, is a truly open, multi-cloud network virtualization and policy management platform. Contrail / OpenContrail SDN stack is integrated with various orchestration systems such as Kubernetes, OpenShift, OpenStack and Mesos, and provides different isolation modes for virtual machines, containers/pods and bare metal workloads

## SUPPORTED ARCHITECTURE

* Contrail SDN installed through OpenShift ansible supports both **SINGLE-MASTER** and **MULTI-MASTER (High-Availability)** configurations 

## COMPONENTS

### Master (Docker Containers)

* Contrail Controller
* Contrail Analytics
* Contrail Analytics Database
* Contrail Kubernetes Manager

### Node (Docker Containers)

* Contrail vRouter Agent
* Contrail Kubernetes Agent

### Node (Kernel Module)

* Contrail vRouter

## INSTALLATION

To install Contrail SDN with OpenShift Enterprise, follow this [install guide](https://github.com/Juniper/contrail-docker/wiki/Red-Hat-OpenShift-with-Contrail-SDN) and set the following configuration parameters in the inventory

Refer to this example [inventory](https://github.com/savithruml/openshift-contrail/blob/master/openshift/install-files/all-in-one/ose-install) file for single-master deployment

Refer to this example [inventory](https://github.com/savithruml/openshift-contrail/blob/master/openshift/install-files/all-in-one/ose-install-ha) file for multi-master HA deployment

#### Set the flag to "false" to disable OVS

        openshift_use_openshift_sdn=false

#### Set this flag to "cni" to use CNI plugins

        os_sdn_network_plugin_name='cni'

#### Set the flag to "true" to install Contrail SDN stack

        openshift_use_contrail=true

#### Set this parameter to the downloaded Contrail SDN image OS

        contrail_os_release=redhat7

#### Set this parameter to the downloaded Contrail SDN image version

        contrail_version=4.1.0.0-8

#### Set Contrail Analytics Database size

        analyticsdb_min_diskgb=50

#### Set Contrail Config Database size

        configdb_min_diskgb=25

#### Set node's physical interface which will be used for Control/data traffic

        vrouter_physical_interface=eno1

#### Set to the path where the Contrail docker image file is located on the ansible host

        contrail_docker_images_path=/root

#### Set CNI version

        cni_version=v0.5.2


### CONTACT

Savithru Lokanath <slokanath@juniper.net>
