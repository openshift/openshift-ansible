## openshift_logging Role

### Please note this role is still a work in progress

This role is used for installing the Aggregated Logging stack. It should be run against
a single host, it will create any missing certificates and API objects that the current
[logging deployer](https://github.com/openshift/origin-aggregated-logging/tree/master/deployer) does.

This role requires that the control host it is run on has Java installed as part of keystore
generation for Elasticsearch (it uses JKS) as well as openssl to sign certificates.

As part of the installation, it is recommended that you add the Fluentd node selector label
to the list of persisted [node labels](https://docs.openshift.org/latest/install_config/install/advanced_install.html#configuring-node-host-labels).

###Required vars:

- `openshift_logging_install_logging`: When `True` the `openshift_logging` role will install Aggregated Logging.
- `openshift_logging_upgrade_logging`:  When `True` the `openshift_logging` role will upgrade Aggregated Logging.

When both `openshift_logging_install_logging` and `openshift_logging_upgrade_logging` are `False` the `openshift_logging` role will uninstall Aggregated Logging.

###Optional vars:

- `openshift_logging_image_prefix`: The prefix for the logging images to use. Defaults to 'docker.io/openshift/origin-'.
- `openshift_logging_image_version`: The image version for the logging images to use. Defaults to 'latest'.
- `openshift_logging_use_ops`: If 'True', set up a second ES and Kibana cluster for infrastructure logs. Defaults to 'False'.
- `openshift_logging_master_url`: The URL for the Kubernetes master, this does not need to be public facing but should be accessible from within the cluster. Defaults to 'https://kubernetes.default.svc.{{openshift.common.dns_domain}}'.
- `openshift_logging_master_public_url`: The public facing URL for the Kubernetes master, this is used for Authentication redirection. Defaults to 'https://{{openshift.common.public_hostname}}:{{openshift.master.api_port}}'.
- `openshift_logging_namespace`: The namespace that Aggregated Logging will be installed in. Defaults to 'logging'.
- `openshift_logging_curator_default_days`: The default minimum age (in days) Curator uses for deleting log records. Defaults to '30'.
- `openshift_logging_curator_run_hour`: The hour of the day that Curator will run at. Defaults to '0'.
- `openshift_logging_curator_run_minute`: The minute of the hour that Curator will run at. Defaults to '0'.
- `openshift_logging_curator_run_timezone`: The timezone that Curator uses for figuring out its run time. Defaults to 'UTC'.
- `openshift_logging_curator_script_log_level`: The script log level for Curator. Defaults to 'INFO'.
- `openshift_logging_curator_log_level`: The log level for the Curator process. Defaults to 'ERROR'.
- `openshift_logging_curator_cpu_limit`: The amount of CPU to allocate to Curator. Default is '100m'.
- `openshift_logging_curator_memory_limit`: The amount of memory to allocate to Curator. Unset if not specified.
- `openshift_logging_curator_nodeselector`: A map of labels (e.g. {"node":"infra","region":"west"} to select the nodes where the curator pod will land.
- `openshift_logging_image_pull_secret`: The name of an existing pull secret to link to the logging service accounts

- `openshift_logging_kibana_hostname`: The Kibana hostname. Defaults to 'kibana.example.com'.
- `openshift_logging_kibana_cpu_limit`: The amount of CPU to allocate to Kibana or unset if not specified.
- `openshift_logging_kibana_memory_limit`: The amount of memory to allocate to Kibana or unset if not specified.
- `openshift_logging_kibana_proxy_debug`: When "True", set the Kibana Proxy log level to DEBUG. Defaults to 'false'.
- `openshift_logging_kibana_proxy_cpu_limit`: The amount of CPU to allocate to Kibana proxy or unset if not specified.
- `openshift_logging_kibana_proxy_memory_limit`: The amount of memory to allocate to Kibana proxy or unset if not specified.
- `openshift_logging_kibana_replica_count`: The number of replicas Kibana should be scaled up to. Defaults to 1.
- `openshift_logging_kibana_nodeselector`: A map of labels (e.g. {"node":"infra","region":"west"} to select the nodes where the pod will land.
- `openshift_logging_kibana_edge_term_policy`: Insecure Edge Termination Policy. Defaults to Redirect.

- `openshift_logging_fluentd_nodeselector`: The node selector that the Fluentd daemonset uses to determine where to deploy to. Defaults to '"logging-infra-fluentd": "true"'.
- `openshift_logging_fluentd_cpu_limit`: The CPU limit for Fluentd pods. Defaults to '100m'.
- `openshift_logging_fluentd_memory_limit`: The memory limit for Fluentd pods. Defaults to '512Mi'.
- `openshift_logging_fluentd_es_copy`: Whether or not to use the ES_COPY feature for Fluentd (DEPRECATED). Defaults to 'False'.
- `openshift_logging_fluentd_use_journal`: NOTE: Fluentd will attempt to detect whether or not Docker is using the journald log driver when using the default of empty.
- `openshift_logging_fluentd_journal_read_from_head`: If empty, Fluentd will use its internal default, which is false.
- `openshift_logging_fluentd_hosts`: List of nodes that should be labeled for Fluentd to be deployed to. Defaults to ['--all'].

- `openshift_logging_es_host`: The name of the ES service Fluentd should send logs to. Defaults to 'logging-es'.
- `openshift_logging_es_port`: The port for the ES service Fluentd should sent its logs to. Defaults to '9200'.
- `openshift_logging_es_ca`: The location of the ca Fluentd uses to communicate with its openshift_logging_es_host. Defaults to '/etc/fluent/keys/ca'.
- `openshift_logging_es_client_cert`: The location of the client certificate Fluentd uses for openshift_logging_es_host. Defaults to '/etc/fluent/keys/cert'.
- `openshift_logging_es_client_key`: The location of the client key Fluentd uses for openshift_logging_es_host. Defaults to '/etc/fluent/keys/key'.

- `openshift_logging_es_cluster_size`: The number of ES cluster members. Defaults to '1'.
- `openshift_logging_es_cpu_limit`:  The amount of CPU limit for the ES cluster.  Unused if not set
- `openshift_logging_es_memory_limit`: The amount of RAM that should be assigned to ES. Defaults to '8Gi'.
- `openshift_logging_es_log_appenders`: The list of rootLogger appenders for ES logs which can be: 'file', 'console'. Defaults to 'file'.
- `openshift_logging_es_pv_selector`: A key/value map added to a PVC in order to select specific PVs.  Defaults to 'None'.
- `openshift_logging_es_pvc_dynamic`: Whether or not to add the dynamic PVC annotation for any generated PVCs. Defaults to 'False'.
- `openshift_logging_es_pvc_size`: The requested size for the ES PVCs, when not provided the role will not generate any PVCs. Defaults to '""'.
- `openshift_logging_es_pvc_prefix`: The prefix for the generated PVCs. Defaults to 'logging-es'.
- `openshift_logging_es_recover_after_time`: The amount of time ES will wait before it tries to recover. Defaults to '5m'.
- `openshift_logging_es_storage_group`: The storage group used for ES. Defaults to '65534'.
- `openshift_logging_es_nodeselector`: A map of labels (e.g. {"node":"infra","region":"west"} to select the nodes where the pod will land.
- `openshift_logging_es_number_of_shards`: The number of primary shards for every new index created in ES. Defaults to '1'.
- `openshift_logging_es_number_of_replicas`: The number of replica shards per primary shard for every new index. Defaults to '0'.

When `openshift_logging_use_ops` is `True`, there are some additional vars. These work the
same as above for their non-ops counterparts, but apply to the OPS cluster instance:
- `openshift_logging_es_ops_host`: logging-es-ops
- `openshift_logging_es_ops_port`: 9200
- `openshift_logging_es_ops_ca`: /etc/fluent/keys/ca
- `openshift_logging_es_ops_client_cert`: /etc/fluent/keys/cert
- `openshift_logging_es_ops_client_key`: /etc/fluent/keys/key
- `openshift_logging_es_ops_cluster_size`: 1
- `openshift_logging_es_ops_cpu_limit`:  The amount of CPU limit for the ES cluster.  Unused if not set
- `openshift_logging_es_ops_memory_limit`: 8Gi
- `openshift_logging_es_ops_pvc_dynamic`: False
- `openshift_logging_es_ops_pvc_size`: ""
- `openshift_logging_es_ops_pvc_prefix`: logging-es-ops
- `openshift_logging_es_ops_recover_after_time`: 5m
- `openshift_logging_es_ops_storage_group`: 65534
- `openshift_logging_kibana_ops_hostname`: The Operations Kibana hostname. Defaults to 'kibana-ops.example.com'.
- `openshift_logging_kibana_ops_cpu_limit`: The amount of CPU to allocate to Kibana or unset if not specified.
- `openshift_logging_kibana_ops_memory_limit`: The amount of memory to allocate to Kibana or unset if not specified.
- `openshift_logging_kibana_ops_proxy_cpu_limit`: The amount of CPU to allocate to Kibana proxy or unset if not specified.
- `openshift_logging_kibana_ops_proxy_memory_limit`: The amount of memory to allocate to Kibana proxy or unset if not specified.
- `openshift_logging_kibana_ops_replica_count`: The number of replicas Kibana ops should be scaled up to. Defaults to 1.

Elasticsearch can be exposed for external clients outside of the cluster.
- `openshift_logging_es_allow_external`: True (default is False) - if this is
  True, Elasticsearch will be exposed as a Route
- `openshift_logging_es_hostname`: The external facing hostname to use for
  the route and the TLS server certificate (default is "es." +
  `openshift_master_default_subdomain`)
- `openshift_logging_es_cert`: The location of the certificate Elasticsearch
  uses for the external TLS server cert (default is a generated cert)
- `openshift_logging_es_key`: The location of the key Elasticsearch
  uses for the external TLS server cert (default is a generated key)
- `openshift_logging_es_ca_ext`: The location of the CA cert for the cert
  Elasticsearch uses for the external TLS server cert (default is the internal
  CA)
Elasticsearch OPS too, if using an OPS cluster:
- `openshift_logging_es_ops_allow_external`: True (default is False) - if this is
  True, Elasticsearch will be exposed as a Route
- `openshift_logging_es_ops_hostname`: The external facing hostname to use for
  the route and the TLS server certificate (default is "es-ops." +
  `openshift_master_default_subdomain`)
- `openshift_logging_es_ops_cert`: The location of the certificate Elasticsearch
  uses for the external TLS server cert (default is a generated cert)
- `openshift_logging_es_ops_key`: The location of the key Elasticsearch
  uses for the external TLS server cert (default is a generated key)
- `openshift_logging_es_ops_ca_ext`: The location of the CA cert for the cert
  Elasticsearch uses for the external TLS server cert (default is the internal
  CA)

### mux - secure_forward listener service
- `openshift_logging_use_mux`: Default `False`.  If this is `True`, a service
  called `mux` will be deployed.  This service will act as a Fluentd
  secure_forward forwarder for the node agent Fluentd daemonsets running in the
  cluster.  This can be used to reduce the number of connections to the
  OpenShift API server, by using `mux` and configuring each node Fluentd to
  send raw logs to mux and turn off the k8s metadata plugin.
- `openshift_logging_mux_allow_external`: Default `False`.  If this is `True`,
  the `mux` service will be deployed, and it will be configured to allow
  Fluentd clients running outside of the cluster to send logs using
  secure_forward.  This allows OpenShift logging to be used as a central
  logging service for clients other than OpenShift, or other OpenShift
  clusters.
- `openshift_logging_use_mux_client`: Default `False`.  If this is `True`, the
  node agent Fluentd services will be configured to send logs to the mux
  service rather than directly to Elasticsearch.
- `openshift_logging_mux_hostname`: Default is "mux." +
  `openshift_master_default_subdomain`.  This is the hostname *external*_
  clients will use to connect to mux, and will be used in the TLS server cert
  subject.
- `openshift_logging_mux_port`: 24284
- `openshift_logging_mux_cpu_limit`: 100m
- `openshift_logging_mux_memory_limit`: 512Mi
- `openshift_logging_mux_default_namespaces`: Default `["mux-undefined"]` - the
 first value in the list is the namespace to use for undefined projects,
 followed by any additional namespaces to create by default - users will
 typically not need to set this
- `openshift_logging_mux_namespaces`: Default `[]` - additional namespaces to
  create for _external_ mux clients to associate with their logs - users will
  need to set this
