#!/bin/bash

MASTERS_LIST="${OCP_CLUSTER_NAME}-master-0.${OCP_BASE_DOMAIN}"
WORKERS_LIST=""
NEW_LINE_SUB="__new_line__"


# Generate masters for inventory
for (( c=1; c<$OCP_MASTERS; c++ ))
do
    MASTERS_LIST="${MASTERS_LIST}${NEW_LINE_SUB}${OCP_CLUSTER_NAME}-master-${c}.${OCP_BASE_DOMAIN}"
done

# Generate masters for inventory
for (( c=0; c<$OCP_WORKERS; c++ ))
do
    WORKERS_LIST="${WORKERS_LIST}${NEW_LINE_SUB}${OCP_CLUSTER_NAME}-worker-${c}.${OCP_BASE_DOMAIN}"
done
export WORKERS_LIST=$WORKERS_LIST
export MASTERS_LIST=$MASTERS_LIST
cat inv.txt.template | envsubst > inventory.txt
sed -i "s/${NEW_LINE_SUB}/\n/g" inventory.txt
