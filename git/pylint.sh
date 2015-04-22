#!/usr/bin/env bash


OLDREV=$1
NEWREV=$2
TRG_BRANCH=$3

/usr/bin/git diff --name-only $OLDREV $NEWREV --diff-filter=ACM | \
 grep ".py$" | \
 xargs -r -I{} pylint --rcfile ${WORKSPACE}/git/.pylintrc  {}

exit $?
