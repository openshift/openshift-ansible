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
image_ids=`docker images -aq`
if test -n "$image_ids"
then
    # Some layers are deleted recursively and are no longer present
    # when docker goes to remove them:
    docker rmi -f `docker images -aq` || true
fi

