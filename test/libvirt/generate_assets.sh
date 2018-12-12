#!/bin/bash
# run this file directly via ./generate_assets.sh; sh generate_assets.sh won't work.

./generate_inventory.sh
cat install-config.yml.template | envsubst > install-config.yml
cat terraform/terraform.tfvars.template | envsubst > terraform/terraform.tfvars
