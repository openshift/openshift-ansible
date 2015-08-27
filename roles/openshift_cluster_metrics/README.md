#openshift_cluster_metrics

This role configures Cluster wide metrics. It does setting up three services:
* Metrics are stored in InfluxDB for querying.
* Heapster reads all nodes and pods from the master, then connects to eachs node's kubelet to retrieve pod metrics.
* Grafan allows users to create dashboards of metrics from InfluxDB

## Requirements

Running OpenShift cluster

## Role Variables

```
# Enable cluster metrics
use_cluster_metrics=true
```

## Dependencies

None

## Example Playbook

TODO

## Security Note
Opening up the read-only port exposes information about the running pods (such as namespace, pod name, labels, etc.) to unauthenticated clients. The requirement to open up this read-only port will be fixed in future versions.

##License

Apache License, Version 2.0

## Author Information

Diego Castro (diego.castro@getupcloud.com)
