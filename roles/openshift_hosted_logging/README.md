###Required vars:

- openshift_hosted_logging_hostname: kibana.example.com
- openshift_hosted_logging_elasticsearch_cluster_size: 1
- openshift_hosted_logging_master_public_url: https://localhost:8443

###Optional vars:
- openshift_hosted_logging_image_prefix: logging image prefix.  No default.  Use this to specify an alternate image repository e.g. my.private.repo:5000/private_openshift/
- target_registry: DEPRECATED - use openshift_hosted_logging_image_prefix instead
- openshift_hosted_logging_image_version: logging image version suffix.  Defaults to the current version of the deployed software.
- openshift_hosted_logging_secret_vars: (defaults to nothing=/dev/null) kibana.crt=/etc/origin/master/ca.crt kibana.key=/etc/origin/master/ca.key ca.crt=/etc/origin/master/ca.crt ca.key=/etc/origin/master/ca.key
- openshift_hosted_logging_fluentd_replicas: (defaults to 1) 3
- openshift_hosted_logging_cleanup: (defaults to no) Set this to 'yes' in order to cleanup logging components instead of deploying.
- openshift_hosted_logging_elasticsearch_instance_ram: Amount of RAM to reserve per ElasticSearch instance (e.g. 1024M, 2G). Defaults to 8GiB; must be at least 512M (Ref.: [ElasticSearch documentation](https://www.elastic.co/guide/en/elasticsearch/guide/current/hardware.html\#\_memory).
- openshift_hosted_logging_elasticsearch_pvc_size: Size of the PersistentVolumeClaim to create per ElasticSearch ops instance, e.g. 100G. If empty, no PVCs will be created and emptyDir volumes are used instead.
- openshift_hosted_logging_elasticsearch_pvc_prefix: Prefix for the names of PersistentVolumeClaims to be created; a number will be appended per instance. If they don't already exist, they will be created with size `openshift_hosted_logging_elasticsearch_pvc_size`.
- openshift_hosted_logging_elasticsearch_pvc_dynamic: Set to `true` to have created PersistentVolumeClaims annotated such that their backing storage can be dynamically provisioned (if that is available for your cluster).
- openshift_hosted_logging_elasticsearch_storage_group: Number of a supplemental group ID for access to Elasticsearch storage volumes; backing volumes should allow access by this group ID (defaults to 65534).
- openshift_hosted_logging_elasticsearch_nodeselector: Specify the nodeSelector that Elasticsearch should be use (label=value)
- openshift_hosted_logging_fluentd_nodeselector: The nodeSelector used to determine which nodes to apply the `openshift_hosted_logging_fluentd_nodeselector_label` label to.
- openshift_hosted_logging_fluentd_nodeselector_label: The label applied to nodes included in the Fluentd DaemonSet. Defaults to "logging-infra-fluentd=true".
- openshift_hosted_logging_kibana_nodeselector: Specify the nodeSelector that Kibana should be use (label=value)
- openshift_hosted_logging_curator_nodeselector: Specify the nodeSelector that Curator should be use (label=value)
- openshift_hosted_logging_enable_ops_cluster: If "true", configure a second ES cluster and Kibana for ops logs.
- openshift_hosted_logging_use_journal: *DEPRECATED - DO NOT USE*
- openshift_hosted_logging_journal_source: By default, if this param is unset or empty, logging will use `/var/log/journal` if it exists, or `/run/log/journal` if not.  You can use this param to force logging to use a different location.
- openshift_hosted_logging_journal_read_from_head: Set to `true` to have fluentd read from the beginning of the journal, to get historical log data.  Default is `false`.  *WARNING* Using `true` may take several minutes or even hours, depending on the size of the journal, until any new records show up in Elasticsearch, and will cause fluentd to consume a lot of CPU and RAM resources.

When `openshift_hosted_logging_enable_ops_cluster` is `True`, there are some
additional vars.  These work the same as above for their non-ops counterparts,
but apply to the OPS cluster instance:
- openshift_hosted_logging_ops_hostname: kibana-ops.example.com
- openshift_hosted_logging_elasticsearch_ops_cluster_size
- openshift_hosted_logging_elasticsearch_ops_instance_ram
- openshift_hosted_logging_elasticsearch_ops_pvc_size
- openshift_hosted_logging_elasticsearch_ops_pvc_prefix
- openshift_hosted_logging_elasticsearch_ops_pvc_dynamic
- openshift_hosted_logging_elasticsearch_ops_nodeselector
- openshift_hosted_logging_kibana_ops_nodeselector
- openshift_hosted_logging_curator_ops_nodeselector
