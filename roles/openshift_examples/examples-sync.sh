#!/bin/bash

# Utility script to update the ansible repo with the latest templates and image
# streams from several github repos
#
# This script should be run from openshift-ansible/roles/openshift_examples

XPAAS_VERSION=ose-v1.3.6
ORIGIN_VERSION=${1:-v1.5}
RHAMP_TAG=1.0.0.GA
RHAMP_TEMPLATE=https://raw.githubusercontent.com/3scale/rhamp-openshift-templates/${RHAMP_TAG}/apicast-gateway/apicast-gateway-template.yml
EXAMPLES_BASE=$(pwd)/files/examples/${ORIGIN_VERSION}
find ${EXAMPLES_BASE} -name '*.json' -delete
TEMP=`mktemp -d`
pushd $TEMP

wget https://github.com/openshift/origin/archive/master.zip -O origin-master.zip
wget https://github.com/jboss-fuse/application-templates/archive/GA.zip -O fis-GA.zip
wget https://github.com/jboss-openshift/application-templates/archive/${XPAAS_VERSION}.zip -O application-templates-master.zip
unzip origin-master.zip
unzip application-templates-master.zip
unzip fis-GA.zip
mv origin-master/examples/db-templates/* ${EXAMPLES_BASE}/db-templates/
mv origin-master/examples/quickstarts/* ${EXAMPLES_BASE}/quickstart-templates/
mv origin-master/examples/jenkins/jenkins-*template.json ${EXAMPLES_BASE}/quickstart-templates/
mv origin-master/examples/image-streams/* ${EXAMPLES_BASE}/image-streams/
mv application-templates-${XPAAS_VERSION}/jboss-image-streams.json ${EXAMPLES_BASE}/xpaas-streams/
# fis content from jboss-fuse/application-templates-GA would collide with jboss-openshift/application-templates
# as soon as they use the same branch/tag names
mv application-templates-GA/fis-image-streams.json ${EXAMPLES_BASE}/xpaas-streams/fis-image-streams.json
mv application-templates-GA/quickstarts/* ${EXAMPLES_BASE}/xpaas-templates/
find application-templates-${XPAAS_VERSION}/ -name '*.json' ! -wholename '*secret*' ! -wholename '*demo*' -exec mv {} ${EXAMPLES_BASE}/xpaas-templates/ \;
wget https://raw.githubusercontent.com/redhat-developer/s2i-dotnetcore/master/dotnet_imagestreams.json         -O ${EXAMPLES_BASE}/image-streams/dotnet_imagestreams.json
wget https://raw.githubusercontent.com/openshift/origin-metrics/master/metrics.yaml                            -O ../openshift_hosted_templates/files/${ORIGIN_VERSION}/origin/metrics-deployer.yaml
wget https://raw.githubusercontent.com/openshift/origin-metrics/enterprise/metrics.yaml                        -O ../openshift_hosted_templates/files/${ORIGIN_VERSION}/enterprise/metrics-deployer.yaml
wget https://raw.githubusercontent.com/openshift/origin-aggregated-logging/master/deployer/deployer.yaml       -O ../openshift_hosted_templates/files/${ORIGIN_VERSION}/origin/logging-deployer.yaml
wget https://raw.githubusercontent.com/openshift/origin-aggregated-logging/enterprise/deployment/deployer.yaml -O ../openshift_hosted_templates/files/${ORIGIN_VERSION}/enterprise/logging-deployer.yaml
wget ${RHAMP_TEMPLATE} -O ${EXAMPLES_BASE}/quickstart-templates/apicast-gateway-template.yml

popd
git diff files/examples
