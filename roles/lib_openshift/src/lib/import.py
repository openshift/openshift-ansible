# pylint: skip-file
# flake8: noqa
'''
   OpenShiftCLI class that wraps the oc commands in a subprocess
'''
# pylint: disable=too-many-lines

from __future__ import print_function
import atexit
import json
import os
import re
import shutil
import subprocess
# pylint: disable=import-error
import ruamel.yaml as yaml
from ansible.module_utils.basic import AnsibleModule
