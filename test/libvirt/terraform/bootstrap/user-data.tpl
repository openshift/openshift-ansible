#cloud-config

# add any ssh public keys
ssh_authorized_keys:
  - "${ssh_authorized_keys}"

runcmd:
  - "echo done"
