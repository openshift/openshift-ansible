# v3.0 to v3.1 upgrade playbook

## Overview
This playbook currently performs the
following steps.

 * Upgrade and restart master services
 * Upgrade and restart node services
 * Modifies the subset of the configuration necessary
 * Applies the latest cluster policies
 * Updates the default router if one exists
 * Updates the default registry if one exists
 * Updates image streams and quickstarts

## Usage
ansible-playbook -i ~/ansible-inventory openshift-ansible/playbooks/byo/openshift-cluster/upgrades/v3_0_to_v3_1/upgrade.yml
