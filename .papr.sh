#!/bin/bash
set -xeuo pipefail

# Essentially use a similar procedure other openshift-ansible PR tests use to
# determine which image tag should be used. This allows us to avoid hardcoding a
# specific version which quickly becomes stale.

if [ -n "${PAPR_BRANCH:-}" ]; then
  target_branch=$PAPR_BRANCH
else
  target_branch=$PAPR_PULL_TARGET_BRANCH
fi
if [[ "${target_branch}" =~ ^release- ]]; then
  target_branch="${target_branch/release-/}"
else
  dnf install -y sed
  target_branch="$( git describe | sed 's/^openshift-ansible-\([0-9]*\.[0-9]*\)\.[0-9]*-.*/\1/' )"
fi

pip install -r requirements.txt

# ping the nodes to check they're responding and register their ostree versions
ansible -vvv -i .papr.inventory nodes -a 'rpm-ostree status'

upload_journals() {
  mkdir journals
  for node in master node1 node2; do
    ssh ocp-$node 'journalctl --no-pager || true' > journals/ocp-$node.log
  done
}

trap upload_journals ERR

# make all nodes ready for bootstrapping
ansible-playbook -vvv -i .papr.inventory playbooks/openshift-node/private/image_prep.yml

# run the actual installer
ansible-playbook -vvv -i .papr.inventory playbooks/deploy_cluster.yml -e "openshift_release=${target_branch}"

### DISABLING TESTS FOR NOW, SEE:
### https://github.com/openshift/openshift-ansible/pull/6132

### # run a small subset of origin conformance tests to sanity
### # check the cluster NB: we run it on the master since we may
### # be in a different OSP network
### ssh ocp-master docker run --rm --net=host --privileged \
###   -v /etc/origin/master/admin.kubeconfig:/config \
###   registry.fedoraproject.org/fedora:27 sh -c \
###     '"dnf install -y origin-tests && \
###       KUBECONFIG=/config /usr/libexec/origin/extended.test --ginkgo.v=1 \
###         --ginkgo.noColor --ginkgo.focus=\"Services.*NodePort|EmptyDir\""'
