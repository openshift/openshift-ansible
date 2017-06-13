#!/bin/bash
set -xeuo pipefail

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
ansible-playbook -vvv -i .papr.inventory playbooks/byo/config.yml

# run a small subset of origin conformance tests to sanity
# check the cluster NB: we run it on the master since we may
# be in a different OSP network
ssh ocp-master docker run --rm --net=host --privileged \
  -v /etc/origin/master/admin.kubeconfig:/config fedora:25 sh -c \
    '"dnf install -y origin-tests && \
      KUBECONFIG=/config /usr/libexec/origin/extended.test --ginkgo.v=1 \
        --ginkgo.noColor --ginkgo.focus=\"Services.*NodePort|EmptyDir\""'
