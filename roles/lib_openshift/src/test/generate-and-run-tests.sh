#!/bin/bash -e

if [[ $# -ne 1 ]] ; then
    echo "Usage: $(basename $0) <master name>"
    exit 1
fi

MASTER=$1


# Put us in the same dir as the script.
cd $(dirname $0)


echo
echo "Running lib_utils generate"
echo "------------------------------"
../../../lib_utils/src/generate.py


echo
echo "Running lib_openshift generate"
echo "------------------------------"
../generate.py


echo
echo "Running lib_openshift Unit Tests"
echo "----------------------------"
cd unit

for test in *.py; do
    echo
    echo "--------------------------------------------------------------------------------"
    echo
    echo "Running $test..."
    ./$test
done


echo
echo "Running lib_openshift Integration Tests"
echo "-----------------------------------"
cd ../integration

for test in *.yml; do
    echo
    echo "--------------------------------------------------------------------------------"
    echo
    echo "Running $test..."
    ./$test -vvv -i "$MASTER," -e cli_master_test="$MASTER" --user=ec2-user --become
done
