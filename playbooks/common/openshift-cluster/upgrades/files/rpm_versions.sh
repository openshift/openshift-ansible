#!/bin/bash

while getopts ":c" opt; do
  case $opt in
    c)
      echo "-c was triggered!" >&2
      containerized="TRUE"
      ;;
    \?)
      echo "Invalid option: -$OPTARG" >&2
      ;;
  esac
done

if [ "${containerized}" == "TRUE" ] ; then
  docker exec atomic-openshift-master rpm -q atomic-openshift 
else
  installed=$(yum list installed -e 0 -q "$@" 2>&1 | tail -n +2 | awk '{ print $2 }' | sort -r | tr '\n' ' ')
  available=$(yum list available -e 0 -q "$@" 2>&1 | tail -n +2 | grep -v 'el7ose' | awk '{ print $2 }' | sort -r | tr '\n' ' ')
fi 

echo "---"
echo "curr_version: ${installed}"
echo "avail_version: ${available}"
