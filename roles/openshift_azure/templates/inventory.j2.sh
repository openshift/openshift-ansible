#!/bin/sh

export AZURE_RESOURCE_GROUPS="{{ openshift_azure_resource_group_name }}"
export AZURE_LOCATIONS="{{ openshift_azure_resource_location }}"
export AZURE_INCLUDE_POWERSTATE="no"
export AZURE_GROUP_BY_RESOURCE_GROUP="yes"
export AZURE_GROUP_BY_LOCATION="no"
export AZURE_GROUP_BY_SECURITY_GROUP="no"
export AZURE_GROUP_BY_TAG="yes"
