#!/bin/bash

# This script installs tox dependencies in the test container
yum install -y gcc libffi-devel python-devel openssl-devel
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py
pip install tox
chmod uga+w /etc/passwd
