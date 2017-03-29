# Deployment Types

This repository supports OpenShift Origin and OpenShift Container Platform.

Various defaults used throughout the playbooks and roles in this repository are
set based on the deployment type configuration (usually defined in an Ansible
hosts file).

The table below outlines the defaults per `openshift_deployment_type`:

| openshift_deployment_type                                       | origin                                   | enterprise (< 3.1)                     | openshift-enterprise (>= 3.1)          |
|-----------------------------------------------------------------|------------------------------------------|----------------------------------------|----------------------------------------|
| **openshift.common.service_type** (also used for package names) | origin                                   | openshift                              |                                        |
| **openshift.common.config_base**                                | /etc/origin                              | /etc/openshift                         | /etc/origin                            |
| **openshift.common.data_dir**                                   | /var/lib/origin                          | /var/lib/openshift                     | /var/lib/origin                        |
| **openshift.master.registry_url openshift.node.registry_url**   | openshift/origin-${component}:${version} | openshift3/ose-${component}:${version} | openshift3/ose-${component}:${version} |
| **Image Streams**                                               | centos                                   | rhel + xpaas                           | rhel                                   |


**NOTES**:

- `enterprise` deployment type is used for OpenShift Enterprise version
3.0.x.
- `openshift-enterprise` deployment type is used for OpenShift Enterprise (and now OpenShift Container Platform) version 3.1 and later.
