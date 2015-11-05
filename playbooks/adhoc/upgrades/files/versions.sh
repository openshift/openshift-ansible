#!/bin/bash

yum_installed=$(yum list installed "$@" | tail -n +2 | grep -v 'Installed Packages' | grep -v 'Red Hat Subscription Management' | awk '{ print $2 }' | tr '\n' ' ')
yum_available=$(yum list available "$@" | tail -n +2 | grep -v 'Available Packages' | grep -v 'Red Hat Subscription Management' | grep -v 'el7ose' | awk '{ print $2 }' | tr '\n' ' ')

echo "---"
echo "curr_version: ${yum_installed}" 
echo "avail_version: ${yum_available}"
