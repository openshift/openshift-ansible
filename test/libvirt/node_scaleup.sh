#!/bin/bash
set -e
APB3="`which python3` `which ansible-playbook`"
WORKDIR=$PWD

cd ../..
$APB3 -vvv -i $WORKDIR/inventory.txt playbooks/openshift-node/scaleup.yml
