# OpenShift Cluster Monitoring Operator

This role installs the OpenShift [Cluster Monitoring Operator](https://github.com/openshift/cluster-monitoring-operator), which manages and updates the Prometheus-based monitoring stack deployed on top of OpenShift.

### **NOTE: This component is unsupported in OCP at this time.**

## Installation

To install the monitoring operator, set this variable:

```yaml
openshift_cluster_monitoring_operator_install: true
```

To uninstall, set:

```yaml
openshift_cluster_monitoring_operator_install: false
```


## Monitoring new components 

To integrate a new OpenShift component with monitoring, follow the [Cluster Monitoring Operator](https://github.com/openshift/cluster-monitoring-operator) docs for contributing new components.

## License

Apache License, Version 2.0
