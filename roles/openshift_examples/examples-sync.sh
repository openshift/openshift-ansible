#!/bin/bash

# Utility script to update the ansible repo with the latest templates and image
# streams from several github repos
#
# This script should be run from openshift-ansible/roles/openshift_examples

XPAAS_VERSION=ose-v1.3.3
ORIGIN_VERSION=${1:-v1.4}
EXAMPLES_BASE=$(pwd)/files/examples/${ORIGIN_VERSION}
find ${EXAMPLES_BASE} -name '*.json' -delete
find ${EXAMPLES_BASE} -name '*.yaml' -delete -exclude registry-console.json
TEMP=`mktemp -d`
pushd $TEMP

wget https://github.com/openshift/origin/archive/master.zip -O origin-master.zip
wget https://github.com/jboss-openshift/application-templates/archive/${XPAAS_VERSION}.zip -O application-templates-master.zip
unzip origin-master.zip
unzip application-templates-master.zip
cp origin-master/examples/db-templates/* ${EXAMPLES_BASE}/db-templates/
cp origin-master/examples/quickstarts/* ${EXAMPLES_BASE}/quickstart-templates/
cp origin-master/examples/jenkins/jenkins-*template.json ${EXAMPLES_BASE}/quickstart-templates/
cp origin-master/examples/image-streams/* ${EXAMPLES_BASE}/image-streams/
mv application-templates-${XPAAS_VERSION}/jboss-image-streams.json ${EXAMPLES_BASE}/xpaas-streams/
find application-templates-${XPAAS_VERSION}/ -name '*.json' ! -wholename '*secret*' ! -wholename '*demo*' -exec mv {} ${EXAMPLES_BASE}/xpaas-templates/ \;
wget https://raw.githubusercontent.com/jboss-fuse/application-templates/master/fis-image-streams.json          -O ${EXAMPLES_BASE}/xpaas-streams/fis-image-streams.json
wget https://raw.githubusercontent.com/redhat-developer/s2i-dotnetcore/master/dotnet_imagestreams.json         -O ${EXAMPLES_BASE}/image-streams/dotnet_imagestreams.json
wget https://raw.githubusercontent.com/openshift/origin-metrics/master/metrics.yaml                            -O ${EXAMPLES_BASE}/infrastructure-templates/origin/metrics-deployer.yaml
wget https://raw.githubusercontent.com/openshift/origin-metrics/enterprise/metrics.yaml                        -O ${EXAMPLES_BASE}/infrastructure-templates/enterprise/metrics-deployer.yaml
wget https://raw.githubusercontent.com/openshift/origin-aggregated-logging/master/deployer/deployer.yaml     -O ${EXAMPLES_BASE}/infrastructure-templates/origin/logging-deployer.yaml
wget https://raw.githubusercontent.com/openshift/origin-aggregated-logging/enterprise/deployment/deployer.yaml -O ${EXAMPLES_BASE}/infrastructure-templates/enterprise/logging-deployer.yaml

popd
git diff files/examples
