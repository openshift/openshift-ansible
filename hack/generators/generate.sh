#!/bin/sh
export PATH=$PATH:$(pwd)/hack/generators
pwd
for file in $(find . -name generate.json); do
  pushd $(dirname $file)
  generate.py --json generate.json
  popd
done
