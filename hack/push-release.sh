#!/bin/bash

# This script pushes all of the built images to a registry.
#
# Set OS_PUSH_BASE_REGISTRY to prefix the destination images
#

set -o errexit
set -o nounset
set -o pipefail

STARTTIME=$(date +%s)
OS_ROOT=$(dirname "${BASH_SOURCE}")/..

PREFIX="${PREFIX:-openshift/origin-ansible}"

# Go to the top of the tree.
cd "${OS_ROOT}"

# Allow a release to be repushed with a tag
tag="${OS_PUSH_TAG:-}"
if [[ -n "${tag}" ]]; then
  tag=":${tag}"
else
  tag=":latest"
fi

# Source tag
source_tag="${OS_TAG:-}"
if [[ -z "${source_tag}" ]]; then
  source_tag="latest"
fi

images=(
  ${PREFIX}
)

PUSH_OPTS=""
if docker push --help | grep -q force; then
  PUSH_OPTS="--force"
fi

if [[ "${OS_PUSH_BASE_REGISTRY-}" != "" || "${tag}" != "" ]]; then
  set -e
  for image in "${images[@]}"; do
    docker tag "${image}:${source_tag}" "${OS_PUSH_BASE_REGISTRY-}${image}${tag}"
  done
  set +e
fi

for image in "${images[@]}"; do
  docker push ${PUSH_OPTS} "${OS_PUSH_BASE_REGISTRY-}${image}${tag}"
done

ret=$?; ENDTIME=$(date +%s); echo "$0 took $(($ENDTIME - $STARTTIME)) seconds"; exit "$ret"
