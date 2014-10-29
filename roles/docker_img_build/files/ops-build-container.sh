#!/bin/bash

RED=$(echo -e "\e[31m")
GREEN=$(echo -e "\e[32m")
YELLOW=$(echo -e "\e[33m")
BLUE=$(echo -e "\e[34m")
NORM=$(echo -e "\e[0m")

CTR_DIR='/usr/local/etc/containers'

EXIT_CODE=0

function main()
{
  # Make sure we're in the directory we expect to be in
  cd $CTR_DIR

  TAG=$(echo $1 | sed 's/_container[\/]*//')
  if [ -z "$TAG" ]
  then
    echo "FAILED parsing tag from \$1 [$1]"
    exit 10
  fi

  docker build --rm -t $TAG $1
  EXIT_CODE=$?
}

if [ $# -ne 1 ]
then
  echo
  echo "  Usage: $(basename $0) container"
  echo "Example: $(basename $0) monitoring_container"
  echo
  exit
fi

if ! [ -d "$CTR_DIR/$1" ]
then
  echo "Error: directory not found [$CTR_DIR/$1]"
  exit 10
fi

time main $@
echo
echo

if [ $EXIT_CODE -eq 0 ]
then
  echo "${GREEN}$1 build succeeded.${NORM}"
else
  echo "${RED}$1 build FAILED!${NORM}"
fi

echo
exit $EXIT_CODE
