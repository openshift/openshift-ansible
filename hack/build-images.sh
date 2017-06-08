#!/bin/bash

set -o errexit
set -o nounset
set -o pipefail

STARTTIME=$(date +%s)
source_root=$(dirname "${0}")/..

prefix="openshift/origin-ansible"
version="latest"
verbose=false
options="-f images/installer/Dockerfile"
help=false

for args in "$@"
do
  case $args in
      --prefix=*)
        prefix="${args#*=}"
        ;;
      --version=*)
        version="${args#*=}"
        ;;
      --no-cache)
        options="${options} --no-cache"
        ;;
      --verbose)
        verbose=true
        ;;
     --help)
        help=true
        ;;
  esac
done

# allow ENV to take precedent over switches
prefix="${PREFIX:-$prefix}"
version="${OS_TAG:-$version}" 

if [ "$help" = true ]; then
  echo "Builds the docker images for openshift-ansible"
  echo
  echo "Options: "
  echo "  --prefix=PREFIX"
  echo "  The prefix to use for the image names."
  echo "  default: openshift/origin-ansible"
  echo
  echo "  --version=VERSION"
  echo "  The version used to tag the image"
  echo "  default: latest"
  echo 
  echo "  --no-cache"
  echo "  If set will perform the build without a cache."
  echo
  echo "  --verbose"
  echo "  Enables printing of the commands as they run."
  echo
  echo "  --help"
  echo "  Prints this help message"
  echo
  exit 0
fi

if [ "$verbose" = true ]; then
  set -x
fi

BUILD_STARTTIME=$(date +%s)
comp_path=$source_root/
docker_tag=${prefix}:${version}
echo
echo
echo "--- Building component '$comp_path' with docker tag '$docker_tag' ---"
docker build ${options} -t $docker_tag $comp_path
BUILD_ENDTIME=$(date +%s); echo "--- $docker_tag took $(($BUILD_ENDTIME - $BUILD_STARTTIME)) seconds ---"
echo
echo

echo
echo
echo "++ Active images"
docker images | grep ${prefix} | grep ${version} | sort
echo


ret=$?; ENDTIME=$(date +%s); echo "$0 took $(($ENDTIME - $STARTTIME)) seconds"; exit "$ret"
