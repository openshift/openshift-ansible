OpenShift/Atomic Enterprise Node
================================

Node service installation

Requirements
------------

* Ansible 2.2
* One or more Master servers
* A RHEL 7.1 host pre-configured with access to the rhel-7-server-rpms,
rhel-7-server-extras-rpms, and rhel-7-server-ose-3.0-rpms repos

Role Variables
--------------

| name                                             | description                                                     | default | required |
|--------------------------------------------------|-----------------------------------------------------------------|---------|----------|
| r_openshift_node_cipher_suites                   |                                                                 |         |          |
| r_openshift_node_cloudprovider_aws_access_key    | AWS access key                                                  | ''      |          |
| r_openshift_node_cloudprovider_aws_secret_key    | AWS secret key                                                  | ''      |          |
| r_openshift_node_cloudprovider_kind              | Cloud provider kind, e.g. aws                                   | ''      |          |
| r_openshift_node_config_base                     | Node configuration base directory, e.g. /etc/origin             |         | true     |
| r_openshift_node_data_dir                        |                                                                 |         | true     |
| r_openshift_node_debug_level                     | Set the default node debug level                                | 2       |          |
| r_openshift_node_deployment_type                 | Deployment type                                                 |         | true     |
| r_openshift_node_disable_swap                    | Set to disable a swap to preserve quality of service guarantees | true    |          |
| r_openshift_node_dns_domain                      |                                                                 |         | true     |
| r_openshift_node_dns_ip                          |                                                                 |         |          |
| r_openshift_node_docker_gte_1_10                 |                                                                 | false   |          |
| r_openshift_node_docker_service_name             | Default docker service name, e.g. docker, container-engine      | docker  |          |
| r_openshift_node_env_vars                        | Set node environment variables                                  | {}      |          |
| r_openshift_node_hostname                        |                                                                 |         | true     |
| r_openshift_node_http_proxy                      | HTTP proxy URL address                                          | ''      |          |
| r_openshift_node_https_proxy                     | HTTPS proxy URL address                                         | ''      |          |
| r_openshift_node_image                           | Node image name to pull for containerized deployment            |         |          |
| r_openshift_node_image_tag                       | Node image tag to pull for containerized deployment             |         | true     |
| r_openshift_node_ip                              |                                                                 |         |          |
| r_openshift_node_iptables_sync_period            |                                                                 |         | true     |
| r_openshift_node_is_atomic                       | Set to deploy a node over AH                                    | false   |          |
| r_openshift_node_is_containerized                | Set to deploy containerized node                                | false   |          |
| r_openshift_node_is_node_system_container        | Set to deploy node system container                             | false   |          |
| r_openshift_node_is_openvswitch_system_container | Set to deploy OVS system container                              | false   |          |
| r_openshift_node_kubelet_args                    | Optionall Kubelet arguments                                     | None    |          |
| r_openshift_node_local_quota_per_fsgroup         |                                                                 |         | true     |
| r_openshift_node_master_api_url                  | Master API URL to query                                         |         | true     |
| r_openshift_node_master_sdn_cluster_network_cidr | SDN Cluster network CIDR set by the master component            |         |          |
| r_openshift_node_min_tls_version                 |                                                                 |         |          |
| r_openshift_node_no_proxy                        | No Proxy                                                        | []      |          |
| r_openshift_node_nodename                        |                                                                 |         | true     |
| r_openshift_node_ovs_image                       | OVS image to pull for containerized deployment                  |         |          |
| r_openshift_node_ovs_system_image                | OVS system image to pull for containerized deployment           |         |          |
| r_openshift_node_pkg_version                     | Node package version to install for package based deployment    | ''      |          |
| r_openshift_node_port_range                      |                                                                 |         |          |
| r_openshift_node_portal_net                      | Portal net                                                      |         |          |
| r_openshift_node_proxy_mode                      |                                                                 |         | true     |
| r_openshift_node_registry_url                    |                                                                 |         | true     |
| r_openshift_node_sdn_mtu                         |                                                                 |         | true     |
| r_openshift_node_sdn_network_plugin_name         |                                                                 |         |          |
| r_openshift_node_service_type                    | System service type                                             |         | true     |
| r_openshift_node_set_node_ip                     |                                                                 | true    |          |
| r_openshift_node_storage_plugin_deps             | List if additional storage plugins to deploy                    | []      |          |
| r_openshift_node_system_image                    | Node system image to pull for system containers deployment      |         |          |
| r_openshift_node_system_images_registry          | System image registry to pull images from                       |         |          |
| r_openshift_node_use_calico                      |                                                                 | false   |          |
| r_openshift_node_use_contiv                      |                                                                 | false   |          |
| r_openshift_node_use_dnsmasq                     |                                                                 | false   |          |
| r_openshift_node_use_nuage                       |                                                                 | false   |          |
| r_openshift_node_use_openshift_sdn               | Set to use OpenShift SDN                                        | true    |          |
| r_openshift_node_version_gte_3_3_or_1_3          |                                                                 | true    |          |
| r_openshift_node_version_gte_3_6                 |                                                                 | true    |          |


From openshift_common:

| Name                          |  Default Value      |                     |
|-------------------------------|---------------------|---------------------|
| openshift_debug_level         | 2                   | Global openshift debug log verbosity |
| openshift_public_ip           | UNDEF (Required)    | Public IP address to use for this host |
| openshift_hostname            | UNDEF (Required)    | hostname to use for this instance |

Dependencies
------------

openshift_common

Example Playbook
----------------

Notes
-----

Currently we support re-labeling nodes but we don't re-schedule running pods nor remove existing labels. That means you will have to trigger the re-schedulling manually. To re-schedule your pods, just follow the steps below:

```
oadm manage-node --schedulable=false ${NODE}
oadm manage-node --drain ${NODE}
oadm manage-node --schedulable=true ${NODE}
````

> If you are using version less than 1.5/3.5 you must replace `--drain` with `--evacuate`.


TODO

License
-------

Apache License, Version 2.0

Author Information
------------------

TODO
