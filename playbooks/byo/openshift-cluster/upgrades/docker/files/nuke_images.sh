#!/bin/bash

# Stop any running containers
running_container_ids=`docker ps -q`
if test -n "$running_container_ids"
then
    docker stop $running_container_ids
fi

# Delete all containers
container_ids=`docker ps -a -q`
if test -n "$container_ids"
then
    docker rm -f -v $container_ids
fi

# Delete all images (forcefully)
image_ids=`docker images -q`
if test -n "$image_ids"
then
    # Taken from: https://gist.github.com/brianclements/f72b2de8e307c7b56689#gistcomment-1443144
    docker rmi $(docker images | grep "$2/\|/$2 \| $2 \|$2 \|$2-\|$2_" | awk '{print $1 ":" $2}') 2>/dev/null || echo "No images matching \"$2\" left to purge."
fi
