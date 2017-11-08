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
* Remove scale group `compute 123`

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
