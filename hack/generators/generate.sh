#!/bin/sh
export PATH=$PATH:$(pwd)/hack/generators
for genfile in $(find . -name generate.json); do
  pushd $(dirname $genfile)
  generate.py --json generate.json
  popd
done
