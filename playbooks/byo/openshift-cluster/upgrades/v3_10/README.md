# v3.10 Major and Minor Upgrade Playbook

## Overview
This playbook currently performs the following steps.

 * Upgrade and restart master services
 * Unschedule node
 * Upgrade and restart docker
 * Upgrade and restart node services
 * Modifies the subset of the configuration necessary
 * Applies the latest cluster policies
 * Updates the default router if one exists
 * Updates the default registry if one exists
 * Updates image streams and quickstarts

## Usage

```
ansible-playbook -i ~/ansible-inventory openshift-ansible/playbooks/byo/openshift-cluster/upgrades/v3_10/upgrade.yml
```
