#!/bin/bash

yum_installed=$(yum list installed -e 0 -q "$@" 2>&1 | tail -n +2 | awk '{ print $2 }' | tr '\n' ' ')

yum_available=$(yum list available -e 0 -q "$@" 2>&1 | tail -n +2 | grep -v 'el7ose' | awk '{ print $2 }' | tr '\n' ' ')

echo "---"
echo "curr_version: ${yum_installed}"
echo "avail_version: ${yum_available}"
