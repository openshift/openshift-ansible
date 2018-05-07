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
target_branch_in=${target_branch}
if [[ "${target_branch}" =~ ^release- ]]; then
  target_branch="${target_branch/release-/}"
else
  dnf install -y sed
  target_branch="$( git describe | sed 's/^openshift-ansible-\([0-9]*\.[0-9]*\)\.[0-9]*-.*/\1/' )"
fi
export target_branch

# Need to define some git variables for rebase.
git config --global user.email "ci@openshift.org"
git config --global user.name "OpenShift Atomic CI"

# Rebase existing branch on the latest code locally, as PAPR running doesn't do merges
git fetch origin ${target_branch_in} && git rebase origin/${target_branch_in}

pip install -r requirements.txt

PAPR_INVENTORY=${PAPR_INVENTORY:-.papr.inventory}
PAPR_RUN_UPDATE=${PAPR_RUN_UPDATE:-0}

# ping the nodes to check they're responding and register their ostree versions
ansible -vvv -i $PAPR_INVENTORY nodes -a 'rpm-ostree status'

upload_journals() {
  mkdir journals
  ansible -vvv -i $PAPR_INVENTORY all \
    -m shell -a 'journalctl --no-pager > /tmp/journal'
  ansible -vvv -i $PAPR_INVENTORY all \
    -m fetch -a "src=/tmp/journal dest=journals/{{ inventory_hostname }}.log flat=yes"
}

trap upload_journals ERR

# Store ansible log separately
export ANSIBLE_LOG_PATH=ansible.log

# run the actual installer
ansible-playbook -v -i $PAPR_INVENTORY playbooks/deploy_cluster.yml

# Run upgrade playbook (to a minor version)
if [[ "${PAPR_RUN_UPDATE:-0}" != "0" ]]; then
  update_version="$(echo $target_branch | sed 's/\./_/')"
  ansible-playbook -v -i $PAPR_INVENTORY playbooks/byo/openshift-cluster/upgrades/v${update_version}/upgrade.yml
fi

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
