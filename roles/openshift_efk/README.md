###Required vars:

- kibana_hostname: kibana.example.com
- es_cluster_size: 1
- master_url: https://localhost:8443

###Optional vars:
- logging_secret_vars: (defaults to nothing=/dev/null) kibana.crt=/etc/origin/master/ca.crt kibana.key=/etc/origin/master/ca.key ca.crt=/etc/origin/master/ca.crt ca.key=/etc/origin/master/ca.key
- fluentd_replicas: (defaults to 1) 3
