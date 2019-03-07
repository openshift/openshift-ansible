#!/usr/bin/python

"""
This callback plugin verifies the required minimum version of Ansible
is installed for proper operation of the OpenShift Ansible Installer.
The plugin is named with leading `aa_` to ensure this plugin is loaded
first (alphanumerically) by Ansible.
"""
import sys
from pkg_resources import parse_version

from ansible import __version__
from ansible.plugins.callback import CallbackBase
from ansible.utils.display import Display


def display(*args, **kwargs):
    """Set up display function for Ansible v2"""
    display_instance = Display()
    display_instance.display(*args, **kwargs)


# Set to minimum required Ansible version
REQUIRED_VERSION = '2.5.7'
DESCRIPTION = "Supported versions: %s or newer" % REQUIRED_VERSION


class CallbackModule(CallbackBase):
    """
    Ansible callback plugin
    """

    CALLBACK_VERSION = 1.0
    CALLBACK_NAME = 'version_requirement'

    def __init__(self):
        """
        Version verification is performed in __init__ to catch the
        requirement early in the execution of Ansible and fail gracefully
        """
        super(CallbackModule, self).__init__()

        if not parse_version(REQUIRED_VERSION) <= parse_version(__version__):
            display(
                'FATAL: Current Ansible version (%s) is not supported. %s'
                % (__version__, DESCRIPTION), color='red')
            sys.exit(1)
