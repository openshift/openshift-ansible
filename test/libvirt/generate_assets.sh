#!/bin/bash
# run this file directly via ./generate_assets.sh; sh generate_assets.sh won't work.

./generate_inventory.sh
cat install-config.yml.template | envsubst > install-config.yml
# Need to make a copy for ansible to reference because install-config.yml is
# consumed/deleted when we generate igintion configs.
cp install-config.yml install-config-ansible.yml
cat terraform/terraform.tfvars.template | envsubst > terraform/terraform.tfvars
