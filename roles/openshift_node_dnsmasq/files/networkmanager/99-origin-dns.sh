#!/bin/bash -x
# -*- mode: sh; sh-indentation: 2 -*-

# This NetworkManager dispatcher script replicates the functionality of
# NetworkManager's dns=dnsmasq  however, rather than hardcoding the listening
# address and /etc/resolv.conf to 127.0.0.1 it pulls the IP address from the
# interface that owns the default route. This enables us to then configure pods
# to use this IP address as their only resolver, where as using 127.0.0.1 inside
# a pod would fail.
#
# To use this,
# - If this host is also a master, reconfigure master dnsConfig to listen on
#   8053 to avoid conflicts on port 53 and open port 8053 in the firewall
# - Drop this script in /etc/NetworkManager/dispatcher.d/
# - systemctl restart NetworkManager
# - Configure node-config.yaml to set dnsIP: to the ip address of this
#   node
#
# Test it:
# host kubernetes.default.svc.cluster.local
# host google.com
#
# TODO: I think this would be easy to add as a config option in NetworkManager
# natively, look at hacking that up

cd /etc/sysconfig/network-scripts
. ./network-functions

[ -f ../network ] && . ../network

if [[ $2 =~ ^(up|dhcp4-change)$ ]]; then
  # If the origin-upstream-dns config file changed we need to restart
  NEEDS_RESTART=0
  UPSTREAM_DNS='/etc/dnsmasq.d/origin-upstream-dns.conf'
  # We'll regenerate the dnsmasq origin config in a temp file first
  UPSTREAM_DNS_TMP=`mktemp`
  UPSTREAM_DNS_TMP_SORTED=`mktemp`
  CURRENT_UPSTREAM_DNS_SORTED=`mktemp`

  ######################################################################
  # couldn't find an existing method to determine if the interface owns the
  # default route
  def_route=$(/sbin/ip route list match 0.0.0.0/0 | awk '{print $3 }')
  def_route_int=$(/sbin/ip route get to ${def_route} | awk '{print $3}')
  def_route_ip=$(/sbin/ip route get to ${def_route} | awk '{print $5}')
  if [[ ${DEVICE_IFACE} == ${def_route_int} && \
       -n "${IP4_NAMESERVERS}" ]]; then
    if [ ! -f /etc/dnsmasq.d/origin-dns.conf ]; then
      cat << EOF > /etc/dnsmasq.d/origin-dns.conf
strict-order
no-resolv
domain-needed
server=/cluster.local/172.30.0.1
server=/30.172.in-addr.arpa/172.30.0.1
EOF
      # New config file, must restart
      NEEDS_RESTART=1
    fi

    ######################################################################
    # Generate a new origin dns config file
    for ns in ${IP4_NAMESERVERS}; do
      if [[ ! -z $ns ]]; then
        echo "server=${ns}"
      fi
    done > $UPSTREAM_DNS_TMP

    # Sort it in case DNS servers arrived in a different order
    sort $UPSTREAM_DNS_TMP > $UPSTREAM_DNS_TMP_SORTED
    sort $UPSTREAM_DNS > $CURRENT_UPSTREAM_DNS_SORTED

    # Compare to the current config file (sorted)
    NEW_DNS_SUM=`md5sum ${UPSTREAM_DNS_TMP_SORTED} | awk '{print $1}'`
    CURRENT_DNS_SUM=`md5sum ${CURRENT_UPSTREAM_DNS_SORTED} | awk '{print $1}'`

    if [ "${NEW_DNS_SUM}" != "${CURRENT_DNS_SUM}" ]; then
      # DNS has changed, copy the temp file to the proper location (-Z
      # sets default selinux context) and set the restart flag
      cp -Z $UPSTREAM_DNS_TMP $UPSTREAM_DNS
      NEEDS_RESTART=1
    fi

    ######################################################################
    if [ "${NEEDS_RESTART}" -eq "1" ]; then
      systemctl restart dnsmasq
    fi

    sed -i '0,/^nameserver/ s/^nameserver.*$/nameserver '"${def_route_ip}"'/g' /etc/resolv.conf

    if ! grep -q '99-origin-dns.sh' /etc/resolv.conf; then
      echo "# nameserver updated by /etc/NetworkManager/dispatcher.d/99-origin-dns.sh" >> /etc/resolv.conf
    fi
  fi

  # Clean up after yourself
  rm -f $UPSTREAM_DNS_TMP $UPSTREAM_DNS_TMP_SORTED $CURRENT_UPSTREAM_DNS_SORTED
fi
