#!/bin/bash

installed=$(yum list installed -e 0 -q "$@" 2>&1 | tail -n +2 | awk '{ print $2 }' | sort -r | tr '\n' ' ')
available=$(yum list available -e 0 -q "$@" 2>&1 | tail -n +2 | grep -v 'el7ose' | awk '{ print $2 }' | sort -r | tr '\n' ' ')

echo "---"
echo "curr_version: ${installed}"
echo "avail_version: ${available}"
