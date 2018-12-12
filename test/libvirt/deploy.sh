#!/bin/bash
#. installrc
./generate_assets.sh
./terraform_provision.sh
./run_ansible.sh
