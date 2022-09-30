#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail

ANSIBLE_POSIX_REPO="https://raw.githubusercontent.com/ansible-collections/ansible.posix"
ANSIBLE_POSIX_MODULES=(callback/profile_tasks.py modules/seboolean.py modules/sysctl.py)
ANSIBLE_POSIX_VERSION=1.4.0

COMMUNITY_GENERAL_REPO="https://raw.githubusercontent.com/ansible-collections/community.general"
COMMUNITY_GENERAL_MODULES=(files/ini_file.py)
COMMUNITY_GENERAL_VERSION=4.8.4

srcdir="$(dirname $0)/.."

pushd ${srcdir}/roles/openshift_node/library

for ap in ${ANSIBLE_POSIX_MODULES[*]} ; do
echo "*** Updating ${ap##*/} from ${ANSIBLE_POSIX_REPO##*/} ${ANSIBLE_POSIX_VERSION}"
curl -sO ${ANSIBLE_POSIX_REPO}/${ANSIBLE_POSIX_VERSION}/plugins/${ap}
done

for cg in ${COMMUNITY_GENERAL_MODULES[*]} ; do
echo "*** Updating ${cg##*/} from ${COMMUNITY_GENERAL_REPO##*/} ${COMMUNITY_GENERAL_VERSION}"
curl -sO ${COMMUNITY_GENERAL_REPO}/${COMMUNITY_GENERAL_VERSION}/plugins/modules/${cg}
done

git --no-pager diff --stat .

popd
