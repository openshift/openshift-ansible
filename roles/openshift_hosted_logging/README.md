###Required vars:

- openshift_hosted_logging_hostname: kibana.example.com
- openshift_hosted_logging_elasticsearch_cluster_size: 1
- openshift_hosted_logging_master_public_url: https://localhost:8443

###Optional vars:
- openshift_hosted_logging_secret_vars: (defaults to nothing=/dev/null) kibana.crt=/etc/origin/master/ca.crt kibana.key=/etc/origin/master/ca.key ca.crt=/etc/origin/master/ca.crt ca.key=/etc/origin/master/ca.key
- openshift_hosted_logging_fluentd_replicas: (defaults to 1) 3
- openshift_hosted_logging_cleanup: (defaults to no) Set this to 'yes' in order to cleanup logging components instead of deploying.
