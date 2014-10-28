#!/bin/bash

echo _
for shared_dir in /etc/haproxy /etc/pki /etc/httpd /var/lib/haproxy
do
  echo "Setting up /shared${shared_dir}..."
  rm -rf $shared_dir
  ln -s /shared${shared_dir} $shared_dir
done
echo _

CTR_CONFIG_FLAG='/shared/var/run/ctr-ipc/flag/ctr_configured'
while ! [ -f "$CTR_CONFIG_FLAG" ]
do
  echo  "Sleeping 10 seconds, waiting for $CTR_CONFIG_FLAG"
  sleep 10
done

# Fix broken sym links
echo "Fixing symlink /etc/httpd/logs..."
ln -sf /var/log/httpd /shared/etc/httpd/logs

echo "Fixing symlink /etc/httpd/modules..."
ln -sf /usr/lib64/httpd/modules /shared/etc/httpd/modules

echo "Fixing symlink /etc/httpd/run..."
ln -sf /var/run/httpd /shared/etc/httpd/run
echo _

echo "Starting supervisord"
exec /usr/bin/supervisord
