#!/bin/bash
set -e

SERVICE_TYPE=$1
DEPLOYMENT_TYPE=$2
VERSION="v${3}"

add_image_version_to_sysconfig () {
    unit_name=$2
    sysconfig_file=/etc/sysconfig/${unit_name}

    if ! grep IMAGE_VERSION ${sysconfig_file}; then
        sed -i "/CONFIG_FILE/a IMAGE_VERSION=${1}" ${sysconfig_file}
    else
        sed -i "s/\(IMAGE_VERSION=\).*/\1${1}/" ${sysconfig_file}
    fi
}

add_image_version_to_unit () {
    deployment_type=$1
    unit_file=$2

    if ! grep IMAGE_VERSION $unit_file; then
        image_namespace="openshift/"
        if [ $deployment_type == "atomic-enterprise" ]; then
            image_namespace="aep3/"
        elif [ $deployment_type == "openshift-enterprise" ]; then
            image_namespace="openshift3/"
        fi

        sed -i "s|\(${image_namespace}[a-zA-Z0-9]\+\)|\1:\${IMAGE_VERSION}|" $unit_file
    fi
}

for unit_file in $(ls /etc/systemd/system/${SERVICE_TYPE}*.service); do
    unit_name=$(basename -s .service ${unit_file})
    add_image_version_to_sysconfig $VERSION $unit_name
    add_image_version_to_unit $DEPLOYMENT_TYPE $unit_file
done

if [ -e /etc/sysconfig/openvswitch ]; then
    add_image_version_to_sysconfig $VERSION openvswitch
else
    echo IMAGE_VERSION=${VERSION} > /etc/sysconfig/openvswitch
fi 
if ! grep EnvironmentFile /etc/systemd/system/openvswitch.service > /dev/null; then
    sed -i "/Service/a EnvironmentFile=/etc/sysconfig/openvswitch" /etc/systemd/system/openvswitch.service
fi
add_image_version_to_unit $DEPLOYMENT_TYPE /etc/systemd/system/openvswitch.service

systemctl daemon-reload
