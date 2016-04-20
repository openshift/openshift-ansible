###Required vars:

- metrics_hostname: metrics-ose.example.com
- metrics_pv_size: 5G "Persistant storage size for Cassandra"


###OPTIONAL

- target_registry: registry.example.com:5000 "Registry to use instead of registry.access.redhat.com"
- openshift_infra_selector: 'nodetype=infra' "Will annotate the openshift-infra namespace to only deploy infrastructure pods od the nodes with teh provided node-selector"
- metrics_secret_vars: (defaults to: nothing=/dev/null) "key=value key=value ..." pairs to give the metrics deployer
