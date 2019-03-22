#!/bin/bash
# run this as sudo
cat << EOF > /etc/NetworkManager/dnsmasq.d/byo-dev.conf
server=/ttb.testing/192.168.128.1
address=/.apps.byo-dev.ttb.testing/192.168.128.21
EOF

systemctl reload NetworkManager
