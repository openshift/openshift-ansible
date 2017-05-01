#!/bin/bash

# Utility script to update the ansible repo with the latest templates and image
# streams from several github repos
#
# This script should be run from openshift-ansible/roles/openshift_examples

XPAAS_VERSION=ose-v1.3.6
ORIGIN_VERSION=${1:-v3.6}
RHAMP_TAG=2.0.0.GA
EXAMPLES_BASE=$(pwd)/files/examples/${ORIGIN_VERSION}
find ${EXAMPLES_BASE} -name '*.json' -delete
TEMP=`mktemp -d`
pushd $TEMP

wget https://github.com/openshift/origin/archive/master.zip -O origin-master.zip
wget https://github.com/jboss-fuse/application-templates/archive/GA.zip -O fis-GA.zip
wget https://github.com/jboss-openshift/application-templates/archive/${XPAAS_VERSION}.zip -O application-templates-master.zip
wget https://github.com/3scale/rhamp-openshift-templates/archive/${RHAMP_TAG}.zip -O amp.zip
unzip origin-master.zip
unzip application-templates-master.zip
unzip fis-GA.zip
unzip amp.zip
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
find 3scale-amp-openshift-templates-${RHAMP_TAG}/ -name '*.yml' -exec mv {} ${EXAMPLES_BASE}/quickstart-templates/ \;
popd

wget https://raw.githubusercontent.com/redhat-developer/s2i-dotnetcore/master/dotnet_imagestreams.json         -O ${EXAMPLES_BASE}/image-streams/dotnet_imagestreams.json
wget https://raw.githubusercontent.com/redhat-developer/s2i-dotnetcore/master/templates/dotnet-example.json           -O ${EXAMPLES_BASE}/quickstart-templates/dotnet-example.json
wget https://raw.githubusercontent.com/redhat-developer/s2i-dotnetcore/master/templates/dotnet-pgsql-persistent.json    -O ${EXAMPLES_BASE}/quickstart-templates/dotnet-pgsql-persistent.json

git diff files/examples
