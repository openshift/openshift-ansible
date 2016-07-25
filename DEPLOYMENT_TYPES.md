#Deployment Types

This module supports OpenShift Origin, OpenShift Enterprise, and Atomic
Enterprise Platform. Each deployment type sets various defaults used throughout
your environment.

The table below outlines the defaults per `deployment_type`.

| deployment_type                                                 | origin                                   | enterprise (< 3.1)                     | atomic-enterprise                | openshift-enterprise (>= 3.1)    |
|-----------------------------------------------------------------|------------------------------------------|----------------------------------------|----------------------------------|----------------------------------|
| **openshift.common.service_type** (also used for package names) | origin                                   | openshift                              | atomic-openshift                 |                                  |
| **openshift.common.config_base**                                | /etc/origin                              | /etc/openshift                         | /etc/origin                      | /etc/origin                      |
| **openshift.common.data_dir**                                   | /var/lib/origin                          | /var/lib/openshift                     | /var/lib/origin                  | /var/lib/origin                  |
| **openshift.master.registry_url openshift.node.registry_url**   | openshift/origin-${component}:${version} | openshift3/ose-${component}:${version} | aos3/aos-${component}:${version} | aos3/aos-${component}:${version} |
| **Image Streams**                                               | centos                                   | rhel + xpaas                           | N/A                              | rhel                             |


**NOTE** `enterprise` deployment type is used for OpenShift Enterprise version
3.0.x OpenShift Enterprise deployments utilizing version 3.1 and later will
make use of the new `openshift-enterprise` deployment type.  Additional work to
migrate between the two will be forthcoming.


