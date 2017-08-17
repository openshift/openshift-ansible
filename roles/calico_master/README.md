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



## Additional Calico/Node and Felix Configuration Options

Additional parameters that can be defined in the inventory are:


| Environment | Description | Schema | Default |   
|---------|----------------------|---------|---------|
| CALICO_IPV4POOL_IPIP | IPIP Mode to use for the IPv4 POOL created at start up.	| off, always, cross-subnet	| always |
| CALICO_LOG_DIR | Directory on the host machine where Calico Logs are written.| String	| /var/log/calico |

### Contact Information

Author: Dan Osborne <dan@projectcalico.org>

For support, join the `#openshift` channel on the [calico users slack](calicousers.slack.com).
