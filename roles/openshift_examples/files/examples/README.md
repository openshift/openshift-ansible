** NOTE ** As of V4 of OpenShift, the Samples Operator (https://github.com/openshift/cluster-samples-operator)
will replace openshift-ansible as the entity responsible for installing example image streams and template into
a OpenShift cluster.  As part of this change, the inventory of of image streams and templates will be pulled
from the curated set of image streams and templates at https://github.com/openshift/library.  OpenShift
development will work to transfer content from this repository to https://github.com/openshift/library during
the initial phases of V4 development.  An update will be made here when that transition period has ended, and
only https://github.com/openshift/library will be utilized.

Image Streams and Templates may require specific versions of OpenShift so
they've been namespaced. At this time, once a new version of Origin is released
the older versions will only receive new content by speficic request.

Please file an issue at https://github.com/openshift/openshift-ansible if you'd
like to see older content updated and have tested to ensure it's backwards
compatible.
