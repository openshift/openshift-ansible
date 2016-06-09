#!/bin/bash

# Stop any running containers
running_container_count=`docker ps -q | wc -l`
if test $running_container_count -gt 0
then
    docker stop $(docker ps -q)
fi

# Delete all containers
container_count=`docker ps -a -q | wc -l`
if test $container_count -gt 0
then
    docker rm -f -v $(docker ps -a -q)
fi

# Delete all images (forcefully)
image_count=`docker images -q | wc -l`
if test $image_count -gt 0
then
    # Taken from: https://gist.github.com/brianclements/f72b2de8e307c7b56689#gistcomment-1443144
    docker rmi $(docker images | grep "$2/\|/$2 \| $2 \|$2 \|$2-\|$2_" | awk '{print $1 ":" $2}') 2>/dev/null || echo "No images matching \"$2\" left to purge."
fi
