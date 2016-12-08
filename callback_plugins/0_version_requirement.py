#!/usr/bin/python

import sys
from ansible import __version__

if __version__ < '2.0':
    from ansible.callbacks import display as pre2_display
    CallbackBase = object

    def display(*args, **kwargs):
        pre2_display(*args, **kwargs)
else:
    from ansible.plugins.callback import CallbackBase
    from ansible.utils.display import Display

    def display(*args, **kwargs):
        display_instance = Display()
        display_instance.display(*args, **kwargs)


# Set to minimum required Ansible version
required_version = '2.2.0.0'
DESCRIPTION = "Supported versions: %s or newer" % required_version


def version_requirement(version):
    return version >= required_version


class CallbackModule(CallbackBase):
    """
    This callback module stops playbook execution if the Ansible
    version is less than required, defined by required_version
    """

    CALLBACK_VERSION = 1.0
    CALLBACK_NAME = 'version_requirement'

    def __init__(self):
        super(CallbackModule, self).__init__()

        if not version_requirement(__version__):
            display(
                'FATAL: Current Ansible version (%s) is not supported. %s'
                % (__version__, DESCRIPTION), color='red')
            sys.exit(1)
