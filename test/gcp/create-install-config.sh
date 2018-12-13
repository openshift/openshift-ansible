#!/bin/sh
#
# This script generates an install-config.yml asset to be consumed by openshift-install
# for setting up a BYOH environment on GCP. This is intended for development purposes only
# and is absolutely unsupported for any purpose.
#
# This script should be run from the root directory of OpenShift-Ansible.


OCP_CLUSTER_NAME=$(whoami)
OCP_PULL_SECRET=$(cat try.openshift.com.json)
OCP_SSH_PUB_KEY=$(cat ~/.ssh/id_rsa.pub)

cat > install-config.yaml <<EOF
baseDomain: origin-gce.dev.openshift.com
clusterID: $(uuidgen --random)
machines:
- name: master
  platform: {}
  replicas: 3
- name: worker
  platform: {}
  replicas: 3
metadata:
  name: ${OCP_CLUSTER_NAME}
networking:
  clusterNetworks:
  - cidr:             10.128.0.0/14
    hostSubnetLength: 9
  serviceCIDR: 172.30.0.0/16
  type:        OpenshiftSDN
platform:
  none: {}
pullSecret: |
  ${OCP_PULL_SECRET}
sshKey: |
  ${OCP_SSH_PUB_KEY}
EOF

cp install-config.yaml install-config.ansible.yaml
