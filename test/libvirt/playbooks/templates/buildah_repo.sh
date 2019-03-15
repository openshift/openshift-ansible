#!/bin/bash

# Execute buildah to scrape rpms from container.

cd /root
cx=$(buildah from {{ easy_openshift_repo_image }})
cx_root=$(buildah mount $cx)

cp $cx_root/* . -r
