OpenShift Configure Nodes
=========

Post installation steps for setting up the cluster

Requirements
------------

None

Role Variables
--------------

| Name                        | Default value     | Description                                                                |
|-----------------------------|-------------------|----------------------------------------------------------------------------|
| ocn_infra_node_filter_key   | "status.capacity" | Key from `osc get nodes -o json` to designate which node is the infra node |
| ocn_infra_node_filter_value | "7232144Ki"       | Value of omp_infra_node_filter_key to filter on |
| ocn_infra_node_label        | "infra"           | The label to apply to the infra node |
| ocn_node_region             | "us-east"         | Region that the none infra nodes are in |

Dependencies
------------

None

Example Playbook
----------------

TODO

License
-------

Apache License, Version 2.0

Author Information
------------------

Wesley Hearn (whearn@redhat.com)
