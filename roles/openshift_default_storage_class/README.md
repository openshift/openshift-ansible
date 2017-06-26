openshift_master_storage_class
=========

A role that deploys configuratons for Openshift StorageClass

Documentation: https://kubernetes.io/docs/concepts/storage/persistent-volumes/

Requirements
------------

None

Role Variables
--------------

openshift_storageclass_name: Name of the storage class to create
openshift_storageclass_provisioner: The kubernetes provisioner to use
openshift_storageclass_parameters: Paramters to pass to the storageclass parameters section


Dependencies
------------


Example Playbook
----------------

  # aws specific
- role: openshift_default_storage_class
  openshift_storageclass_name: awsEBS
  openshift_storageclass_provisioner: kubernetes.io/aws-ebs
  openshift_storageclass_parameters:
    type: gp2
    encripted: true



License
-------

Apache

Author Information
------------------

Openshift Operations
