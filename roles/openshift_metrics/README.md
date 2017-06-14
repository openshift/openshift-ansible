OpenShift Metrics with Hawkular
====================

OpenShift Metrics Installation

Requirements
------------
This role has the following dependencies:

- Java is required on the control node to generate keystores for the Java components
- httpd-tools is required on the control node to generate various passwords for the metrics components

The following variables need to be set and will be validated:

- `openshift_metrics_hawkular_hostname`: hostname used on the hawkular metrics route.

- `openshift_metrics_project`: project (i.e. namespace) where the components will be
  deployed.


Role Variables
--------------

For default values, see [`defaults/main.yaml`](defaults/main.yaml).

- `openshift_metrics_image_prefix`: Specify prefix for metrics components; e.g for
  "openshift/origin-metrics-deployer:v1.1", set prefix "openshift/origin-".

- `openshift_metrics_image_version`: Specify version for metrics components; e.g. for
  "openshift/origin-metrics-deployer:v1.1", set version "v1.1".

- `openshift_metrics_hawkular_cert:` The certificate used for re-encrypting the route
  to Hawkular metrics.  The certificate must contain the hostname used by the route.
  The default router certificate will be used if unspecified

- `openshift_metrics_hawkular_key:` The key used with the Hawkular certificate

- `openshift_metrics_hawkular_ca:` An optional certificate used to sign the Hawkular certificate.

- `openshift_metrics_hawkular_replicas:` The number of replicas for Hawkular metrics.

- `openshift_metrics_cassandra_replicas`: The number of Cassandra nodes to deploy for the
  initial cluster.

- `openshift_metrics_cassandra_storage_type`: Use `emptydir` for ephemeral storage (for
  testing), `pv` to use persistent volumes (which need to be created before the
  installation) or `dynamic` for dynamic persistent volumes.

- `openshift_metrics_cassandra_pvc_prefix`: The name of persistent volume claims created
  for cassandra will be this with a serial number appended to the end, starting
  from 1.

- `openshift_metrics_cassandra_pvc_size`: The persistent volume claim size for each of the
  Cassandra  nodes.

- `openshift_metrics_heapster_standalone`: Deploy only heapster, without the Hawkular Metrics and
  Cassandra components.

- `openshift_metrics_heapster_allowed_users`: A comma-separated list of CN to accept.  By
  default, this is set to allow the OpenShift service proxy to connect.  If you
  override this, make sure to add `system:master-proxy` to the list in order to
  allow horizontal pod autoscaling to function properly.

- `openshift_metrics_startup_timeout`: How long in seconds we should wait until
  Hawkular Metrics and Heapster starts up before attempting a restart.

- `openshift_metrics_duration`: How many days metrics should be stored for.

- `openshift_metrics_resolution`: How often metrics should be gathered.

- `openshift_metrics_install_hawkular_agent`: Install the Hawkular OpenShift Agent (HOSA). HOSA can be used
  to collect custom metrics from your pods. This component is currently in tech-preview and is not installed by default.

## Additional variables to control resource limits
Each metrics component (hawkular, cassandra, heapster) can specify a cpu and memory limits and requests by setting
the corresponding role variable:
```
openshift_metrics_<COMPONENT>_(limits|requests)_(memory|cpu): <VALUE>
```
e.g
```
openshift_metrics_cassandra_limits_memory: 1Gi
openshift_metrics_hawkular_requests_cpu: 100
```

Dependencies
------------
openshift_facts


Example Playbook
----------------

```
- name: Configure openshift-metrics
  hosts: oo_first_master
  roles:
  - role: openshift_metrics
```

License
-------

Apache License, Version 2.0

Author Information
------------------

Jose David Martín (j.david.nieto@gmail.com)
