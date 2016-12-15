OpenShift Metrics with Hawkular
====================

OpenShift Metrics Installation

Requirements
------------

The following variables need to be set and will be validated:

- `openshift_metrics_hostname`: hostname used on the hawkular metrics route.

- `openshift_metrics_project`: project (i.e. namespace) where the components will be
  deployed.


Role Variables
--------------

For default values, see [`defaults/main.yaml`](defaults/main.yaml).

- `openshift_metrics_image_prefix`: Specify prefix for metrics components; e.g for
  "openshift/origin-metrics-deployer:v1.1", set prefix "openshift/origin-".

- `openshift_metrics_image_version`: Specify version for metrics components; e.g. for
  "openshift/origin-metrics-deployer:v1.1", set version "v1.1".

- `openshift_metrics_master_url`: Internal URL for the master, for authentication retrieval.

- `openshift_metrics_hawkular_user_write_access`: If user accounts should be able to write
  metrics.  Defaults to 'false' so that only Heapster can write metrics and not
  individual users.  It is recommended to disable user write access, if enabled
  any user will be able to write metrics to the system which can affect
  performance and use Cassandra disk usage to unpredictably increase.

- `openshift_metrics_hawkular_replicas:` The number of replicas for Hawkular metrics.

- `openshift_metrics_cassandra_nodes`: The number of Cassandra Nodes to deploy for the
  initial cluster.

- `openshift_metrics_cassandra_storage_type`: Use `emptydir` for ephemeral storage (for
  testing), `pv` to use persistent volumes (which need to be created before the
  installation) or `dynamic` for dynamic persistent volumes.

- `openshift_metrics_cassandra_pv_prefix`: The name of persistent volume claims created
  for cassandra will be this with a serial number appended to the end, starting
  from 1.

- `openshift_metrics_cassandra_pv_size`: The persistent volume size for each of the
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
