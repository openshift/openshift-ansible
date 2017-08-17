# Calico

Configure Calico components for the Master host.

## Requirements

* Ansible 2.2

## Installation

To install, set the following inventory configuration parameters:

* `openshift_use_calico=True`
* `openshift_use_openshift_sdn=False`
* `os_sdn_network_plugin_name='cni'`

For more information, see [Calico's official OpenShift Installation Documentation](https://docs.projectcalico.org/latest/getting-started/openshift/installation#bring-your-own-etcd)

## Improving security with BYO-etcd

By default, Calico uses the etcd set up by OpenShift. To accomplish this, it generates and distributes client etcd certificates to each node.
Distributing these certs across the cluster in this way weakens the overall security,
so Calico should not be deployed in production in this mode.

Instead, Calico can be installed in BYO-etcd mode, where it connects to an externally
set up etcd. For information on deploying Calico in BYO-etcd mode, see 
[Calico's official OpenShift Installation Documentation](https://docs.projectcalico.org/latest/getting-started/openshift/installation#bring-your-own-etcd)

## Calico Configuration Options

Additional parameters that can be defined in the inventory are:

| Environment | Description | Schema | Default |   
|---------|----------------------|---------|---------|
| CALICO_IPV4POOL_IPIP | IPIP Mode to use for the IPv4 POOL created at start up.	| off, always, cross-subnet	| always |
| CALICO_LOG_DIR | Directory on the host machine where Calico Logs are written.| String	| /var/log/calico |

### Contact Information

Author: Dan Osborne <dan@projectcalico.org>

For support, join the `#openshift` channel on the [calico users slack](calicousers.slack.com).
