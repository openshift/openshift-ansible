#!/bin/bash

set -x

# Argument 1: path to openshift-ansible/playbooks
# Argument 2: inventory path
# Argument 3: Extra vars path

echo "Running prerequisites"

ansible-playbook -vv            \
                 --inventory $2 \
                 --e @$3        \
                 $1/prerequisites.yml

echo "Running network_manager setup"

playbook_base='/usr/share/ansible/openshift-ansible/playbooks/'
if [[ -s "$1/openshift-node/network_manager.yml" ]]; then
   playbook="$1/openshift-node/network_manager.yml"
else
   playbook="$1/byo/openshift-node/network_manager.yml"
fi
ansible-playbook -vv            \
                 --inventory $1 \
                 --e @$2        \
                ${playbook}

echo "Running openshift-ansible deploy_cluster"

ansible-playbook -vv            \
                 --inventory $2 \
                 --e @$3        \
                 $1/deploy_cluster.yml
