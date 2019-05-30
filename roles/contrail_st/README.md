# Contrail SDN

[Contrail Networking](https://www.juniper.net/us/en/products-services/sdn/contrail/contrail-networking/), based on [TungstenFabric](https://tungstenfabric.io/) project, is a truly open, multi-cloud network virtualization and policy management platform. Contrail / TungstenFabric SDN stack is integrated with various orchestration systems such as Kubernetes, OpenShift, OpenStack and Mesos, and provides different isolation modes for virtual machines, containers/pods and bare metal workloads.

## SUPPORTED ARCHITECTURE

* Contrail SDN installed through OpenShift ansible supports both non-HA and  HA configurations.

## CONTRAIL SOFTWARE COMPONENTS

### Contrail Master (DaemonSets)

- **Contrail Image Installer**: Downloads all contrail container images if not present.
- **Contrail Controller Config**: The config daemonset consists of all config components
  like contrail service monitor, schema transformer, api server etc which are running as
  a docker container.
- **Contrail Controller Control**: The contrail controller is installed by this daemonset.
- **Contrail Controller WebUI**: WebUI components are deployed here. We use port 8143.
- **Contrail Analytics**: All Contrail analytics components like the analytics collector,
  topology, alarm-gen are installed by this daemonset.
- **Contrail Analytics Database**: Contrail Analytics uses this container as its DB.
- **Contrail Config DB Node Manager**: Node Manager for Config DB, Node manager containers are run
  by all Contrail components to provide current status.
- **Contrail Config DB**: DB used by the Contrail Controller Config component.
- **Contrail Kubernetes Manager**: The interface between the Openshift API server and
  Contrail Controller.

Note:  These Contrail components are installed on the infra-node.

### Nodes (DaemonSets)
- **Contrail Agent**: As part of the agent pod we install the **vrouter kernel module** and the **contrail-cni**.

### Contrail Ansible Roles

* **Contrail common**: This role contains common functions which are required by other contrail roles
* **Contrail master**: Preps up by creating all daemonsets.
* **Contrail st**: Preps the contrail schema transformer.

## INSTALLATION

To install Contrail SDN with OpenShift Enterprise, follow this [install guide](https://github.com/Juniper/contrail-kubernetes-docs)

Refer to this example [openshift 3.11 contrail installation](https://github.com/Juniper/contrail-kubernetes-docs/blob/master/install/openshift/3.11/standalone-openshift.md) for non-HA/HA deployments

### CONTACT

Pragash Vijayaragavan <pvijayaragav@juniper.net>
