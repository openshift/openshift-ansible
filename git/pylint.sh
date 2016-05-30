#!/usr/bin/env bash
set -eu

ANSIBLE_UPSTREAM_FILES=(
    'inventory/aws/hosts/ec2.py'
    'inventory/gce/hosts/gce.py'
    'inventory/libvirt/hosts/libvirt_generic.py'
    'inventory/openstack/hosts/nova.py'
    'lookup_plugins/sequence.py'
    'playbooks/gce/openshift-cluster/library/gce.py'
  )

OLDREV=$1
NEWREV=$2
#TRG_BRANCH=$3

PYTHON=$(which python)

set +e
PY_DIFF=$(/usr/bin/git diff --name-only $OLDREV $NEWREV --diff-filter=ACM | grep ".py$")
set -e

FILES_TO_TEST=""

for PY_FILE in $PY_DIFF; do
  IGNORE_FILE=false
  for UPSTREAM_FILE in "${ANSIBLE_UPSTREAM_FILES[@]}"; do
    if [ "${PY_FILE}" == "${UPSTREAM_FILE}" ]; then
      IGNORE_FILE=true
      break
    fi
  done

  if [ "${IGNORE_FILE}" == true ]; then
    echo "Skipping file ${PY_FILE} as an upstream Ansible file..."
    continue
  fi

  if [ -e "${PY_FILE}" ]; then
    FILES_TO_TEST="${FILES_TO_TEST} ${PY_FILE}"
  fi
done

export PYTHONPATH=${WORKSPACE}/utils/src/:${WORKSPACE}/utils/test/

if [ "${FILES_TO_TEST}" != "" ]; then
  echo "Testing files: ${FILES_TO_TEST}"
  exec ${PYTHON} -m pylint --rcfile ${WORKSPACE}/git/.pylintrc ${FILES_TO_TEST}
else
  exit 0
fi
