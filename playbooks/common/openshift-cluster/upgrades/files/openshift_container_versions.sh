#!/bin/bash

# Here we don't really care if this is a master, api, controller or node image.
# We just need to know the version of one of them.
unit_file=$(ls /etc/systemd/system/${1}*.service | grep -v node-dep | head -n1)

if [ ${1} == "origin" ]; then
    image_name="openshift/origin"
elif grep aep $unit_file 2>&1 > /dev/null; then
    image_name="aep3/node"
elif grep openshift3 $unit_file 2>&1 > /dev/null; then
    image_name="openshift3/node"
fi

installed=$(docker run --rm --entrypoint=/bin/openshift ${image_name} version 2> /dev/null | grep openshift | awk '{ print $2 }' | cut -f1 -d"-" | tr -d 'v')

docker pull ${image_name} 2>&1 > /dev/null
available=$(docker run --rm --entrypoint=/bin/openshift ${image_name} version 2> /dev/null | grep openshift | awk '{ print $2 }' | cut -f1 -d"-" | tr -d 'v')

echo "---"
echo "curr_version: ${installed}"
echo "avail_version: ${available}"
