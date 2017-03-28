# Calico (Master)

Configure Calico components for the Master host.

## Requirements

* Ansible 2.2

## Warning: This Calico Integration is in Alpha

Calico shares the etcd instance used by OpenShift, and distributes client etcd certificates to each node.
For this reason, **we do not (yet) recommend running Calico on any production-like
cluster, or using it for any purpose besides early access testing.**

## Installation

To install, set the following inventory configuration parameters:

* `openshift_use_calico=True`
* `openshift_use_openshift_sdn=False`
* `os_sdn_network_plugin_name='cni'`


### Contact Information

Author: Dan Osborne <dan@projectcalico.org>

For support, join the `#openshift` channel on the [calico users slack](calicousers.slack.com).
