#!/bin/bash

# Utility script to update the ansible repo with the latest templates and image
# streams from several github repos
#
# This script should be run from openshift-ansible/roles/openshift_examples

EXAMPLES_BASE=$(pwd)/files/examples
find files/examples -name '*.json' -delete
TEMP=`mktemp -d`
pushd $TEMP
wget https://github.com/openshift/origin/archive/master.zip -O origin-master.zip
wget https://github.com/openshift/django-ex/archive/master.zip -O django-ex-master.zip
wget https://github.com/openshift/rails-ex/archive/master.zip -O rails-ex-master.zip
wget https://github.com/openshift/nodejs-ex/archive/master.zip -O nodejs-ex-master.zip
wget https://github.com/openshift/dancer-ex/archive/master.zip -O dancer-ex-master.zip
wget https://github.com/openshift/cakephp-ex/archive/master.zip -O cakephp-ex-master.zip
wget https://github.com/jboss-openshift/application-templates/archive/master.zip -O application-templates-master.zip
unzip origin-master.zip
unzip django-ex-master.zip
unzip rails-ex-master.zip
unzip nodejs-ex-master.zip
unzip dancer-ex-master.zip
unzip cakephp-ex-master.zip
unzip application-templates-master.zip
cp origin-master/examples/db-templates/* ${EXAMPLES_BASE}/db-templates/
cp origin-master/examples/image-streams/* ${EXAMPLES_BASE}/image-streams/
cp django-ex-master/openshift/templates/* ${EXAMPLES_BASE}/quickstart-templates/
cp rails-ex-master/openshift/templates/* ${EXAMPLES_BASE}/quickstart-templates/
cp nodejs-ex-master/openshift/templates/* ${EXAMPLES_BASE}/quickstart-templates/
cp dancer-ex-master/openshift/templates/* ${EXAMPLES_BASE}/quickstart-templates/
cp cakephp-ex-master/openshift/templates/* ${EXAMPLES_BASE}/quickstart-templates/
mv application-templates-master/jboss-image-streams.json ${EXAMPLES_BASE}/xpaas-streams/
find application-templates-master/ -name '*.json' ! -wholename '*secret*' -exec mv {} ${EXAMPLES_BASE}/xpaas-templates/ \;
popd
git diff files/examples
