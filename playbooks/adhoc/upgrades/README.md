# [NOTE]
This playbook will re-run installation steps overwriting any local
modifications. You should ensure that your inventory has been updated with any
modifications you've made after your initial installation. If you find any items
that cannot be configured via ansible please open an issue at
https://github.com/openshift/openshift-ansible

# Overview
This playbook is available as a technical preview. It currently performs the
following steps.

 * Upgrade and restart master services
 * Upgrade and restart node services
 * Applies latest configuration by re-running the installation playbook
 * Applies the latest cluster policies
 * Updates the default router if one exists
 * Updates the default registry if one exists
 * Updates image streams and quickstarts

# Usage
ansible-playbook -i ~/ansible-inventory openshift-ansible/playbooks/adhoc/upgrades/upgrade.yml
