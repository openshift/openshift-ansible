RHEL Subscribe
==============

Subscribes the RHEL servers and add the OpenShift enterprise repos.

Role variables
--------------

### `rhsub_user`

Username for the subscription-manager.

### `rhsub_pass`

Password for the subscription-manager.

### `rhsub_pool`

Name of the pool to attach (optional).

### `rhsub_server`

Custom hostname for the Satellite server (optional).

### `openshift_release`

Version for the OpenShift Enterprise repositories.

Example: `3.6`
