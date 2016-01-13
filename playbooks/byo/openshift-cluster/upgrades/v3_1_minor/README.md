# v3.1 minor upgrade playbook
This upgrade will preserve all locally made configuration modifications to the
Masters and Nodes.

## Overview
This playbook is available as a technical preview. It currently performs the
following steps.

 * Upgrade and restart master services
 * Upgrade and restart node services
 * Applies the latest cluster policies
 * Updates the default router if one exists
 * Updates the default registry if one exists
 * Updates image streams and quickstarts

## Usage
ansible-playbook -i ~/ansible-inventory openshift-ansible/playbooks/byo/openshift-cluster/upgrades/v3_1_minor/upgrade.yml
