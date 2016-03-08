#!/bin/bash

# Here we don't really care if this is a master, api, controller or node image.
# We just need to know the version of one of them.
unit_file=$(ls /etc/systemd/system/${1}*.service | head -n1)
installed_container_name=$(basename -s .service ${unit_file})
installed=$(docker exec ${installed_container_name} openshift version | grep openshift | awk '{ print $2 }' | cut -f1 -d"-" | tr -d 'v')

if [ ${1} == "origin" ]; then
    image_name="openshift/origin"
elif grep aep $unit_file 2>&1 > /dev/null; then
    image_name="aep3/aep"
elif grep ose $unit_file 2>&1 > /dev/null; then
    image_name="openshift3/ose"
fi

docker pull ${image_name} 2>&1 > /dev/null
available=$(docker run --rm ${image_name} version | grep openshift | awk '{ print $2 }' | cut -f1 -d"-" | tr -d 'v')

echo "---"
echo "curr_version: ${installed}"
echo "avail_version: ${available}"
