#!/bin/bash
set -xeuo pipefail

# F25 currently has 2.2.1, so install from pypi
pip install ansible==2.2.2.0

# do a simple ping to make sure the nodes are available
ansible -vvv -i .redhat-ci.inventory nodes -a 'rpm-ostree status'

upload_journals() {
  mkdir journals
  for node in master node1 node2; do
    ssh ocp-$node 'journalctl --no-pager || true' > journals/ocp-$node.log
  done
}

trap upload_journals ERR

# run the actual installer
ansible-playbook -vvv -i .redhat-ci.inventory playbooks/byo/config.yml

# run a small subset of origin conformance tests to sanity
# check the cluster NB: we run it on the master since we may
# be in a different OSP network
ssh ocp-master docker run --rm --net=host --privileged \
  -v /etc/origin/master/admin.kubeconfig:/config fedora:25 sh -c \
    '"dnf install -y origin-tests && \
      KUBECONFIG=/config /usr/libexec/origin/extended.test --ginkgo.v=1 \
        --ginkgo.noColor --ginkgo.focus=\"Services.*NodePort|EmptyDir\""'
