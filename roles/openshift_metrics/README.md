OpenShift Metrics with Hawkular
====================

OpenShift Metrics Installation

Requirements
------------

The following variables need to be set and will be validated:

- `metrics_hostname`: hostname used on the hawkular metrics route.

- `metrics_project`: project (i.e. namespace) where the components will be
  deployed.


Role Variables
--------------

For default values, see [`defaults/main.yaml`](defaults/main.yaml).

- `image_prefix`: Specify prefix for metrics components; e.g for
  "openshift/origin-metrics-deployer:v1.1", set prefix "openshift/origin-".

- `image_version`: Specify version for metrics components; e.g. for
  "openshift/origin-metrics-deployer:v1.1", set version "v1.1".

- `master_url`: Internal URL for the master, for authentication retrieval.

- `hawkular_user_write_access`: If user accounts should be able to write
  metrics.  Defaults to 'false' so that only Heapster can write metrics and not
  individual users.  It is recommended to disable user write access, if enabled
  any user will be able to write metrics to the system which can affect
  performance and use Cassandra disk usage to unpredictably increase.

- `hawkular_cassandra_nodes`: The number of Cassandra Nodes to deploy for the
  initial cluster.

- `hawkular_cassandra_storage_type`: Use `emptydir` for ephemeral storage (for
  testing), `pv` to use persistent volumes (which need to be created before the
  installation) or `dynamic` for dynamic persistent volumes.

- `hawkular_cassandra_pv_prefix`: The name of persistent volume claims created
  for cassandra will be this with a serial number appended to the end, starting
  from 1.

- `hawkular_cassandra_pv_size`: The persistent volume size for each of the
  Cassandra  nodes.

- `heapster_standalone`: Deploy only heapster, without the Hawkular Metrics and
  Cassandra components.

- `heapster_allowed_users`: A comma-separated list of CN to accept.  By
  default, this is set to allow the OpenShift service proxy to connect.  If you
  override this, make sure to add `system:master-proxy` to the list in order to
  allow horizontal pod autoscaling to function properly.

- `metrics_duration`: How many days metrics should be stored for.

- `metrics_resolution`: How often metrics should be gathered.


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
