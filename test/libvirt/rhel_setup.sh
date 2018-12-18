#!/bin/bash
set -e
APB3="`which python3` `which ansible-playbook`"
WORKDIR=$PWD

# Need system packages.
$APB3 -i $WORKDIR/inventory.txt ~/git/aos-ansible/playbooks/aws_install_prep.yml
$APB3 -i $WORKDIR/inventory.txt $WORKDIR/playbooks/rhel_prep.yml -vvv
#$APB3 -i $WORKDIR/inventory.txt $WORKDIR/playbooks/localrepo.yml -vvv
