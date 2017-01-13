# pylint: skip-file
# flake8: noqa
'''
   OpenShiftCLI class that wraps the oc commands in a subprocess
'''
# pylint: disable=too-many-lines


import atexit
import json
import os
import re
import ruamel.yaml as yaml
import shutil
import subprocess
from ansible.module_utils.basic import AnsibleModule
