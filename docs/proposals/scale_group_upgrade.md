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

The current playbooks in openshift ansible create autoscaling groups for infra/compute and 
allow for custom groups as well.  This code lives in `role/openshift_aws`.

Assume we are upgrading the compute node group:
compute 123

The upgrade process would look like this:
* Create a new scale group `compute 456`
* Scale up the new scale group to match the first groups capacity
* Allow nodes to join the cluster by approving node CSRs
* Set the nodes from `compute 123` as unschedulable
* Drain the `compute 123` pods from the nodes
* Determine if we want to role back to `compute 123` or continue on with `compute 456`.
* Remove scale group `compute 123` or `compute 456`

## Benefits

There are many benefits to this approach.

* Treat the scale groups as immutable infrastructure
* Roll back strategy is as simple as scaling the old scale group back to capacity
* Managing hosts can be done by scale group or by scale group tags

## Downside

* Managing the compute name or version
* Risk of removing scale groups
* Process surrounding acceptance of nodes (not specific to this strategy)

## User Story
As an admin of OpenShift-Ansible,
I want to upgrade my scale groups
so that I can receive product updates, CVE remediations, and provide a path forward for customers.

## Acceptance Criteria
* Verify that a new scale group is created
* Verify that the old scale group properly drained
* Verify that the old scale group is removed
* Verify that the old launch config is removed
* Verify there is documentation about the process

## References


## Workflow

Outline of a typical workflow for an upgrade.
* An AMI is built with a specific version of openshift
  This is done through openshift-ansible/playbooks/aws/openshift-cluster/build_ami.yml playbook.
  Specify the correct repository location and version via the following vars:
  openshift_pkg_version=
  openshift_additional_repositories=[]
* The output of the build_ami should be an AMI that is placed in the AWS account.
  The following upgrade playbooks will handle the AMI in two ways:
  * If the openshift_aws_ami is specified then the scale groups will use the specific id.
  * If multiple AMIs are desired then you can place them in the the openshift_aws_ami_map:
  ```
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
  and infra groups. In order for the upgrade to process correctly, you will specify 
  the current_version and new_version variables.  These are used to generate the 
  launch config and the scale group name.
  ```
  openshift_aws_current_version: ''
  openshift_aws_new_version: ''
  ```

  Theorethically, what this upgrade will look like is the following:
  ```
  launch_config=clusterid-type-version
  e.g: opstest-compute-3.7.4.1

  scale group=clusterid openshift type version
  e.g: opstest openshift 3.7.4.1


  current_version=3.7.4.1
  new_version=3.7.4.2

  For more information on which variables are available for provisioning, they can be
  found inside of roles/openshift_aws/defaults/main.yml

* If any extra groups are desired the user can specify them.  The groups are driven by dictionaries with the
  key of the instance in each dictionary aligning all of the variables.  In the example below the
  name of the dictionary key is `compute-crio`.  The AMI, node group, and security groups are all joined
  by this dictionary key.

  ```
  # specify the desired 
  openshift_aws_ami_map_extra:
    compute-crio: ami-c53ebbbf
  openshift_aws_node_group_config_extra:
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
        version: "{{ openshift_aws_new_version }}"
        runtime: cri-o
      termination_policy: "{{ openshift_aws_node_group_termination_policy }}"
      replace_all_instances: "{{ openshift_aws_node_group_replace_all_instances }}"

  openshift_aws_launch_config_security_groups_extra:
    compute-crio:
    - "{{ openshift_aws_clusterid }}"  # default sg
    - "{{ openshift_aws_clusterid }}_compute"  # node type sg
    - "{{ openshift_aws_clusterid }}_compute_k8s"  # node type sg k8s
  
  ```
