#!/bin/bash
set -xeuo pipefail

pip install requests

query_github() {
    repo=$1; shift
    resource=$1; shift
    python -c "
import sys
import requests
j = requests.get('https://api.github.com/repos/$repo/$resource').json()
for q in sys.argv[1:]:
    if q.isdigit():
        q = int(q)
    j = j[q]
print(j)" "$@"
}

# Essentially use a similar procedure other openshift-ansible PR tests use to
# determine which image tag should be used. This allows us to avoid hardcoding a
# specific version which quickly becomes stale.

if [ -n "${PAPR_BRANCH:-}" ]; then
    target_branch=$PAPR_BRANCH
else
    # check which branch we're targeting if we're a PR
    target_branch=$(query_github $PAPR_REPO pulls/$PAPR_PULL_ID base ref)
    [ -n "$target_branch" ]
fi

# this is a bit wasteful, though there's no easy way to say "only clone up to
# the first tag in the branch" -- ideally, PAPR could help with caching here
git clone --branch $target_branch --single-branch https://github.com/openshift/origin
export OPENSHIFT_IMAGE_TAG=$(git -C origin describe --abbrev=0)

echo "Targeting OpenShift Origin $OPENSHIFT_IMAGE_TAG"

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

# run the actual installer
# FIXME: override openshift_image_tag defined in the inventory until
# https://github.com/openshift/openshift-ansible/issues/4478 is fixed.
ansible-playbook -vvv -i .papr.inventory playbooks/byo/config.yml -e "openshift_image_tag=$OPENSHIFT_IMAGE_TAG"

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
