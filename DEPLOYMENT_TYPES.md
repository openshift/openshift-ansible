#Deployment Types

This module supports OpenShift Origin and OpenShift Enterprise. Each deployment
type sets various defaults used throughout your environment.

The table below outlines the defaults per `deployment_type`.

| deployment_type                                                 | origin                                   | openshift-enterprise |
|-----------------------------------------------------------------|------------------------------------------|----------------------|
| **openshift.common.service_type** (also used for package names) | origin                                   |  atomic-openshift    |
| **openshift.common.config_base**                                | /etc/origin                              | /etc/origin          |
| **openshift.common.data_dir**                                   | /var/lib/origin                          | /var/lib/origin      |
| **openshift.master.registry_url openshift.node.registry_url**   | openshift/origin-${component}:${version} | openshift3/ose-${component}:${version} |
| **Image Streams**                                               | centos                                   | rhel + xpaas         |

