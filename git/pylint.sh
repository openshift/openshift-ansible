#!/usr/bin/env bash


OLDREV=$1
NEWREV=$2
TRG_BRANCH=$3

PYTHON=/var/lib/jenkins/python27/bin/python

/usr/bin/git diff --name-only $OLDREV $NEWREV --diff-filter=ACM | \
 grep ".py$" | \
 xargs -r -I{} ${PYTHON} -m pylint --rcfile ${WORKSPACE}/git/.pylintrc  {}

exit $?
