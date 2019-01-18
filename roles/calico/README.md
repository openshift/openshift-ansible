# Calico

Installs and configures Calico for networking and policy.

## Requirements

* Ansible 2.2

## Installation

To install Calico, set the following inventory configuration parameters:

* `openshift_use_calico=True`
* `openshift_use_openshift_sdn=False`
* `os_sdn_network_plugin_name='cni'`

## Calico configuration options

### Configuring etcd access

By default, Calico will share the etcd used by OpenShift.
To configure Calico to use a separate instance of etcd, place etcd SSL client certs on your master,
then set the following variables in your inventory.ini:

* `calico_etcd_ca_cert_file=/path/to/etcd-ca.crt`
* `calico_etcd_cert_file=/path/to/etcd-client.crt`
* `calico_etcd_key_file=/path/to/etcd-client.key`
* `calico_etcd_endpoints=https://etcd:2379`

### Configuring IP pools

By default, Calico will use the IP pool defined in `roles/calico/default/main.yaml`, enabling IP-in-IP encapsulation
and using the CIDR defined in `openshift_cluster_network_cidr` for pod IP addresses.

The set of IP pools to use can be configured by overriding the `ip_pools` variable when running ansible, setting it to the
full list of desired IP pools.

For example, if `pools.yaml` contains the desired `ip_pools`:

	ansible-playbook -i inventory.ini <playbook> --extra-vars "@pools.yaml"

### Additional configuration options

Additional parameters that can be defined in the inventory are:

| Environment | Description | Schema | Default |
|---------|----------------------|---------|---------|
| CALICO_LOG_DIR | Directory on the host machine where Calico Logs are written.| String	| /var/log/calico |

## Upgrading from older versions

OpenShift-Ansible installs Calico as a self-hosted install. Previously, Calico ran as a systemd service. Running Calico
in this manner is now deprecated, and must be upgraded to a hosted cluster. Please run the Legacy Upgrade playbook to
upgrade your existing Calico deployment to a hosted deployment:

        ansible-playbook -i inventory.ini playbooks/byo/calico/legacy_upgrade.yml

### Contact information

Author: Dan Osborne <dan@projectcalico.org>

For support, join the `#openshift` channel on the [calico users slack](calicousers.slack.com).
