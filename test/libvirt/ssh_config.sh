#!/bin/bash

cat << EOF >> ~/.ssh/config
Host *.ttb.testing
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
EOF
