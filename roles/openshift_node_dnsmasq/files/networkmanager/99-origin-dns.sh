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
# - Drop this script in /etc/NetworkManager/dispatcher.d/
# - systemctl restart NetworkManager
# - Configure node-config.yaml to set dnsIP: to the ip address of this
#   node
#
# dnsmasq will bind to all interfaces except lo by default
# If you want to bind to specific interfaces set OPENSHIFT_NODE_DNSMASQ_INTERFACES
# to the comma separated list of interfaces you wish to bind to
#
# Test it:
# host kubernetes.default.svc.cluster.local
# host google.com
#
# TODO: I think this would be easy to add as a config option in NetworkManager
# natively, look at hacking that up

cd /etc/sysconfig/network-scripts
. ./network-functions
. /etc/sysconfig/atomic-openshift-node

[ -f ../network ] && . ../network

if [[ $2 =~ ^(up|dhcp4-change|dhcp6-change)$ ]]; then
  NEEDS_RESTART=0
  NEW_RESOLV_CONF=`mktemp`
  if [ ! -f /etc/origin/node/resolv.conf ]; then
    cp /etc/resolv.conf /etc/origin/node/resolv.conf
  fi
  ######################################################################
  # couldn't find an existing method to determine if the interface owns the
  # default route
  def_route=$(/sbin/ip route list match 0.0.0.0/0 | awk '{print $3 }')
  def_route_int=$(/sbin/ip route get to ${def_route} | awk '{print $3}')
  def_route_ip=$(/sbin/ip route get to ${def_route} | awk '{print $5}')
  if [[ ${DEVICE_IFACE} == ${def_route_int} ]]; then
    if [ ! -f /etc/dnsmasq.d/origin-dns.conf ]; then
      cat << EOF > /etc/dnsmasq.d/origin-dns.conf
domain-needed
enable-dbus
bind-interfaces
dns-loop-detect
resolv-file=/etc/origin/node/resolv.conf
except-interface=lo
EOF
      if [ ! -z $OPENSHIFT_NODE_DNSMASQ_INTERFACES ]; then
        interfaces=$(echo $OPENSHIFT_NODE_DNSMASQ_INTERFACES | tr "," "\n")
        echo "${interfaces[@]}"
        for i in $interfaces; do
          echo "interface=${i}" >> /etc/dnsmasq.d/origin-dns.conf
        done
      fi

      # New config file, must restart
      NEEDS_RESTART=1
    fi

    # dnsmasq not running, needs a restart
    if ! `systemctl -q is-active dnsmasq.service`; then
      NEEDS_RESTART=1
    fi

    ######################################################################
    if [ "${NEEDS_RESTART}" -eq "1" ]; then
      systemctl restart dnsmasq
    fi

    # Only if dnsmasq is running properly make it our only nameserver and place
    # a watermark on /etc/resolv.conf
    if `systemctl -q is-active dnsmasq.service`; then
      if ! grep -q '99-origin-dns.sh' /etc/resolv.conf; then
          echo "# nameserver updated by /etc/NetworkManager/dispatcher.d/99-origin-dns.sh" >> ${NEW_RESOLV_CONF}
      fi
      sed -e '/^nameserver.*$/d' /etc/resolv.conf >> ${NEW_RESOLV_CONF}
      echo "nameserver "${def_route_ip}"" >> ${NEW_RESOLV_CONF}
      if ! grep -qw search ${NEW_RESOLV_CONF}; then
        echo 'search cluster.local' >> ${NEW_RESOLV_CONF}
      elif ! grep -q 'search.*cluster.local' ${NEW_RESOLV_CONF}; then
        sed -i '/^search/ s/$/ cluster.local/' ${NEW_RESOLV_CONF}
      fi
      cp -Z ${NEW_RESOLV_CONF} /etc/resolv.conf
    fi
  fi

  # Clean up after yourself
  rm -f $NEW_RESOLV_CONF
fi
