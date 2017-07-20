# The role deploys Elasticsearch cluster on top of OpenShift

## Topology

The deployment supports 2 kinds of node roles at the moment:
* master
* data-client

We explicitly don't support combining masters with any other node type.
`es_node_topology` variable holds the description of the cluster node
topology.

### Masters

`es_node_topology.masters` describes how many masters will run. Single
DeploymentConfig will be created for all masters.
`replicas` field define how many masters to spin up (replicas in Kubernetes
notation).
`limits` define Kubernetes pod limits
`nodeSelector` define Kuberenetes pod selector

### Client Data nodes

`es_node_topology.clientdata` is an array that describes how each data client is structured. Each entry in the array corresponds to individual DeploymentConfig.
`limits` define Kubernetes pod limits
`nodeSelector` define Kuberenetes pod selector

# Deployment

## Prerequisites

### Node assignment

It is highly recommended that the nodes where Elasticsearch is run are labelled
appropriately. Including the nodes for master and client pods, then the
appropriate `nodeSelector` is used in the topology.

### Virtual memory

Host-level setting `vm.max_map_count=262144` is required on all the nodes where
Elasticsearch pods will be run.
https://www.elastic.co/guide/en/elasticsearch/reference/5.3/vm-max-map-count.html

### Host-mount settings for data nodes

In case `hostmount` option is used, create mount points on the data nodes
prior to starting the deployment.
Mount point permissions: make sure that everyone in group `root` has all the
permissions.

Label the folder appropriately:

`# chcon -Rt svirt_sandbox_file_t <dir_name>`

for details please consult with : http://www.projectatomic.io/blog/2015/06/using-volumes-with-docker-can-cause-problems-with-selinux/

## Execute deployment

Define the node topology (`es_node_topology` var), define namespace.

Define storage that you're going to use for Elasticsearch:
* PersistentVolumeClaim - type `pvc`.
* Ephemeral - type `emptydir`
* Host-mounted directories - type `hostmount`

Run the role.

## Upgrade

TODO: needs to be implemented.
