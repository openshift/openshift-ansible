# Deployment Types

This repository supports OpenShift Origin and OpenShift Container Platform.

Various defaults used throughout the playbooks and roles in this repository are
set based on the deployment type configuration (usually defined in an Ansible
hosts file).

The table below outlines the defaults per `openshift_deployment_type`:

| openshift_deployment_type                                       | origin                                   | openshift-enterprise                   |
|-----------------------------------------------------------------|------------------------------------------|----------------------------------------|
| **openshift_service_type** (also used for package names)        | origin                                   | atomic-openshift                       |
| **openshift.common.config_base**                                | /etc/origin                              | /etc/origin                            |
| **openshift_data_dir**                                          | /var/lib/origin                          | /var/lib/origin                        |
| **Image Streams**                                               | centos                                   | rhel                                   |
