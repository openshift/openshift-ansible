# Proposal Title

## Description
With the direction of moving to golden images (AMIs), there is a need to design the
upgrade path for scale groups.

## Rationale
We currently provide an upgrade path for in-place upgrades.  We also need to provide a path
for golden images when placed in scale groups.

## Design
The core principle here is to take advantage of the immutable infrastructure that is provided
when working with golden images.

The current playbooks in openshift ansible create autoscaling groups for infra/compute.
 This code lives in `role/openshift_aws`.

The current scale groups that get created are managed by the following variable:
```
openshift_aws_node_groups:
- name: "{{ openshift_aws_clusterid }} compute group"
  group: compute
- name: "{{ openshift_aws_clusterid }} infra group"
  group: infra

openshift_aws_created_asgs: []
openshift_aws_current_asgs: []
```

The main idea here is that we model a deploymentconfig and a replication controller inside of openshift.  This means that for each scale group found in the above `openshift_aws_node_groups` we store a tag `deployment_serial` which keeps track of the current deployment.  When a new scale group is created the deployment serial is set to 1.  If an upgrade is occuring then we create a new scale group with the name of the node group with the deployment variable, e.g. `testcluster compute group 1`.  An upgrade of this group would look like this: e.g. `testcluster compute group 2`.

Here we will walk through the logic in the upgrade playbooks.

Assume we are upgrading the compute node group:
testcluster compute group

The upgrade process would look like this.  For simplicity we will assume the `openshift_aws_node_groups` includes only a single group for compute.
* Query AWS for the compute node group to determine if there is one that matches the tags `{'host-type': 'node', 'sub-host-type': compute, 'runtime': docker}`.
* If one is not found, we create a new group named, `testcluster compute group 1` and create a tag named `deployment_serial` and set it to 1. We place the new scale group into a list, `openshift_aws_created_asgs`.
* If one matches, we look for a tag named `deployment_serial` on the match.  We increment this number and create a new scale group using this number in the name: `testcluster compute group 2`.  We place the query results into the current scale group list, `openshift_aws_current_asgs`.  We place the new scale group into a separate list, `openshift_aws_created_asgs`.
* If more than 1 is found then we fail.
* Wait until the new scale group reaches capacity
* Allow nodes to join the cluster by approving node CSRs
* Set the nodes from `openshift_aws_current_asgs` as unschedulable
* Drain the pods from `openshift_aws_current_asgs` nodes
* Determine if we want to roll back to `openshift_aws_current_asgs` or continue on with `openshift_aws_created_asgs`.
* Remove scale group `openshift_aws_current_asgs` or `openshift_aws_created_asgs`

## Benefits

There are many benefits to this approach.

* Treat the scale groups as immutable infrastructure
* Roll back strategy is as simple as scaling the old scale group back to capacity or recreating the new scale group and setting the luanch config to point at the previous AMI id.
* Managing hosts can be done by scale group or by scale group tags

## Downside

* Risk of removing scale groups
* Rely on AWS API to query hosts and state.
* Process surrounding acceptance of nodes (not specific to this strategy)

## User Story
As an admin of OpenShift-Ansible,
I want to upgrade my scale groups
so that I can receive product updates, CVE remediations, and provide a path forward for customers.

## Acceptance Criteria
* Verify that a new scale group is created
* Verify that the old scale group properly drained
* Verify that the old scale group is removed
* Verify there is documentation about the process

## References


## Workflow

Outline of a typical workflow for an upgrade.
* An AMI is built with a specific version of openshift.
  This is done through openshift-ansible/playbooks/aws/openshift-cluster/build_ami.yml playbook.
  Specify the correct repository location and version via the following vars if required:
  ```
  openshift_additional_repositories=[]
  #openshift_pkg_version=
  #openshift_image_tag=
  #openshift_release=
  ```
* The output of the build_ami should be an AMI that is placed in the AWS account.
  The following upgrade playbooks will handle the AMI in two ways:
  * If the openshift_aws_ami is specified then the scale groups will use the specific id.
  * If multiple AMIs are desired then you can place them in the the `openshift_aws_ami_map`.  This
    variable is a place holder for the node group type and it maps to the `openshift_aws_ami`. Below
    is an example of how that map works:
  ```
  openshift_aws_ami: ami-123456

  openshift_aws_ami_map:
    master: "{{ openshift_aws_ami }}"
    infra: "{{ openshift_aws_ami }}"
    compute: "{{ openshift_aws_ami }}"
  ```
  * If the openshift_aws_ami is unspecified, the AWS code will search for the latest
    AMI with the following name and use it:
  ```
  openshift_aws_ami_name: openshift-gi
  ```
* The next step is to perform the update on the scale node groups.  The node scale groups are
  inventory driven.  By default there are two groups that are created which are compute
  and infra groups. These are used to generate the launch config and the scale group name.

  Theorethically, what this upgrade will look like is the following:
  ```
  openshift_aws_node_groups:
  - name: "{{ openshift_aws_clusterid }} compute group"
    group: compute
  ```

  These should create the following objects in this format: 

  A launch config with the following name:
  ```
  `openshift_aws_node_group.name`-`AMI ID`-`epoch timestamp`
  e.g: opstest compute group-ami-1234567-1513004600
  ```

  A scale group with the following name:
  ```
  `openshift_aws_node_group.name` `deployment_serial`
  e.g: opstest compute group 1

  ```

  For more information on which variables are available for provisioning, they can be
  found inside of roles/openshift_aws/defaults/main.yml.

* If additional scale groups are desired then the user can specify them with inventory variables. To do so, specify 
  the new groups inside of the openshift_aws_node_gorups array.
  The group key in each dictionary element of the array is what joins the data inside of the other configuration dictionaries.  Here is an example of
  an extra group with the name of `compute-crio`.  The AMI, node group, and security groups are all joined
  by this dictionary key, `compute-crio`.

  ```
  openshift_aws_node_groups:
  - name: openshift compute-crio group
    group: compute-crio

  # specify the desired
  openshift_aws_ami_map:
    compute-crio: ami-c53ebbbf

  openshift_aws_node_group_config:
    compute-crio:
      instance_type: m4.xlarge
      volumes: "{{ openshift_aws_node_group_config_node_volumes }}"
      health_check:
        period: 60
        type: EC2
      min_size: 3
      max_size: 100
      desired_size: 3
      tags:
        host-type: node
        sub-host-type: compute
        runtime: cri-o
      termination_policy: "{{ openshift_aws_node_group_termination_policy }}"
      replace_all_instances: "{{ openshift_aws_node_group_replace_all_instances }}"

  openshift_aws_launch_config_security_groups_extra:
    compute-crio:
    - "{{ openshift_aws_clusterid }}"  # default sg
    - "{{ openshift_aws_clusterid }}_compute"  # node type sg
    - "{{ openshift_aws_clusterid }}_compute_k8s"  # node type sg k8s
  ```
