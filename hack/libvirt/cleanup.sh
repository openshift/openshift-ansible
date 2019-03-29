#!/bin/bash
rm .openshift* -f
rm *.ign -f
cd terraform/
terraform destroy -auto-approve
