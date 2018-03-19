#!/bin/sh

set -euo pipefail

# Use a playbook to calculate the inventory dynamically from
# the provided cluster variables.
src="$(dirname "$(readlink -f "$0")")"
if ! out="$( ansible-playbook --inventory-file "${src}/none" ${src}/../../../playbooks/azure/openshift-cluster/inventory.yml 2>&1 )"; then
  echo "error: Inventory configuration failed" 1>&2
  echo "$out" 1>&2
  echo "{}"
  exit 1
fi
. "/tmp/azure-inventory.sh"
exec ${src}/hosts.py
