#!/bin/bash

# Utility script to update the ansible repo with the latest templates and image
# streams from several github repos
#
# This script should be run from openshift-ansible/roles/openshift_examples

XPAAS_VERSION=ose-v1.4.8-1
ORIGIN_VERSION=${1:-v3.9}
ORIGIN_BRANCH=${2:-master}
RHAMP_TAG=2.0.0.GA
EXAMPLES_BASE=$(pwd)/files/examples/${ORIGIN_VERSION}
find ${EXAMPLES_BASE} -name '*.json' -delete
TEMP=`mktemp -d`
pushd $TEMP

if [ ! -d "${EXAMPLES_BASE}" ]; then
  mkdir -p ${EXAMPLES_BASE}
fi
wget https://github.com/openshift/origin/archive/${ORIGIN_BRANCH}.zip -O origin.zip
wget https://github.com/jboss-fuse/application-templates/archive/GA.zip -O fis-GA.zip
wget https://github.com/jboss-openshift/application-templates/archive/${XPAAS_VERSION}.zip -O application-templates-master.zip
wget https://github.com/3scale/rhamp-openshift-templates/archive/${RHAMP_TAG}.zip -O amp.zip
unzip origin.zip
unzip application-templates-master.zip
unzip fis-GA.zip
unzip amp.zip
mv origin-${ORIGIN_BRANCH}/examples/db-templates/* ${EXAMPLES_BASE}/db-templates/
mv origin-${ORIGIN_BRANCH}/examples/quickstarts/* ${EXAMPLES_BASE}/quickstart-templates/
mv origin-${ORIGIN_BRANCH}/examples/jenkins/jenkins-*template.json ${EXAMPLES_BASE}/quickstart-templates/
mv origin-${ORIGIN_BRANCH}/examples/image-streams/* ${EXAMPLES_BASE}/image-streams/
mv application-templates-${XPAAS_VERSION}/jboss-image-streams.json ${EXAMPLES_BASE}/xpaas-streams/
# fis content from jboss-fuse/application-templates-GA would collide with jboss-openshift/application-templates
# as soon as they use the same branch/tag names
mv application-templates-GA/fis-image-streams.json ${EXAMPLES_BASE}/xpaas-streams/fis-image-streams.json
mv application-templates-GA/quickstarts/* ${EXAMPLES_BASE}/xpaas-templates/
find application-templates-${XPAAS_VERSION}/ -name '*.json' ! -wholename '*secret*' ! -wholename '*demo*' -exec mv {} ${EXAMPLES_BASE}/xpaas-templates/ \;
find 3scale-amp-openshift-templates-${RHAMP_TAG}/ -name '*.yml' -exec mv {} ${EXAMPLES_BASE}/quickstart-templates/ \;
popd

wget https://raw.githubusercontent.com/redhat-developer/s2i-dotnetcore/master/dotnet_imagestreams.json         -O ${EXAMPLES_BASE}/image-streams/dotnet_imagestreams.json
wget https://raw.githubusercontent.com/redhat-developer/s2i-dotnetcore/master/dotnet_imagestreams_centos.json         -O ${EXAMPLES_BASE}/image-streams/dotnet_imagestreams_centos.json
wget https://raw.githubusercontent.com/redhat-developer/s2i-dotnetcore/master/templates/dotnet-example.json           -O ${EXAMPLES_BASE}/quickstart-templates/dotnet-example.json
wget https://raw.githubusercontent.com/redhat-developer/s2i-dotnetcore/master/templates/dotnet-pgsql-persistent.json    -O ${EXAMPLES_BASE}/quickstart-templates/dotnet-pgsql-persistent.json
wget https://raw.githubusercontent.com/redhat-developer/s2i-dotnetcore/master/templates/dotnet-runtime-example.json    -O ${EXAMPLES_BASE}/quickstart-templates/dotnet-runtime-example.json

git diff files/examples
