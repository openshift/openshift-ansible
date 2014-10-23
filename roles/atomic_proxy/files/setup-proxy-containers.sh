#!/bin/bash

function fail {
  msg=$1
  echo
  echo $msg
  echo
  exit 5
}


NUM_DATA_CTR=$(docker ps -a | grep -c proxy-shared-data-1)
[ "$NUM_DATA_CTR" -ne 0 ] && fail "ERROR: proxy-shared-data-1 exists"


# pre-cache the container images
echo
timeout --signal TERM --kill-after 30 600  docker pull busybox:latest  || fail "ERROR: docker pull of busybox failed"

echo
# WORKAROUND: Setup the shared data container
/usr/bin/docker run --name "proxy-shared-data-1"  \
          -v /shared/etc/haproxy                  \
          -v /shared/etc/httpd                    \
          -v /shared/etc/openshift                \
          -v /shared/etc/pki                      \
          -v /shared/var/run/ctr-ipc              \
          -v /shared/var/lib/haproxy              \
          -v /shared/usr/local                    \
          "busybox:latest" true

# WORKAROUND: These are because we're not using a pod yet
cp /usr/local/etc/ctr-proxy-1.service /usr/local/etc/ctr-proxy-puppet-1.service /usr/local/etc/ctr-proxy-monitoring-1.service /etc/systemd/system/

systemctl daemon-reload

echo
echo -n "sleeping 10 seconds for systemd reload to take affect..."
sleep 10
echo " Done."

# Start the services
systemctl start ctr-proxy-puppet-1 ctr-proxy-1 ctr-proxy-monitoring-1
