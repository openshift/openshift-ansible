# Kube-Router

Configure Kube-Router components for the Master host.

## Installation

To install, set the following inventory configuration parameters:

* `openshift_use_kube_router=True`
* `openshift_use_openshift_sdn=False`
* `os_sdn_network_plugin_name='cni'`

More info
https://github.com/cloudnativelabs/kube-router/blob/master/docs/generic.md
