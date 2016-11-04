#!/bin/bash

# Utility script to update the ansible repo with the latest templates for
# metrics and logging
#
# This script should be run from
# openshift-ansible/roles/openshift_hosted_templates

ORIGIN_VERSION=v1.4
EXAMPLES_BASE=$(pwd)/files/${ORIGIN_VERSION}
find ${EXAMPLES_BASE} -name '*.json' -delete
TEMP=`mktemp -d`
pushd $TEMP

wget https://raw.githubusercontent.com/openshift/origin-metrics/master/metrics.yaml                            -O ${EXAMPLES_BASE}/origin/metrics-deployer.yaml
wget https://raw.githubusercontent.com/openshift/origin-metrics/enterprise/metrics.yaml                        -O ${EXAMPLES_BASE}/enterprise/metrics-deployer.yaml
wget https://raw.githubusercontent.com/openshift/origin-aggregated-logging/master/deployer/deployer.yaml     -O ${EXAMPLES_BASE}/origin/logging-deployer.yaml
wget https://raw.githubusercontent.com/openshift/origin-aggregated-logging/enterprise/deployment/deployer.yaml -O ${EXAMPLES_BASE}/enterprise/logging-deployer.yaml

popd
git diff files
