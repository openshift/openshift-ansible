#!/bin/bash

if [ $# -ne 1 ]
then
  echo
  echo "Usage: $(basename $0) <container_name>"
  echo
  exit 1
fi

PID=$(docker inspect --format '{{.State.Pid}}' $1)

nsenter --target $PID --mount --uts --ipc --net --pid
