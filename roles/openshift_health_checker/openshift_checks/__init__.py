"""
Health checks for OpenShift clusters.
"""

import os
from abc import ABCMeta, abstractmethod, abstractproperty
from importlib import import_module

import six


class OpenShiftCheckException(Exception):
    """Raised when a check cannot proceed."""
    pass


@six.add_metaclass(ABCMeta)
class OpenShiftCheck(object):
    """A base class for defining checks for an OpenShift cluster environment."""

    def __init__(self, module_executor):
        self.module_executor = module_executor

    @abstractproperty
    def name(self):
        """The name of this check, usually derived from the class name."""
        return "openshift_check"

    @classmethod
    def is_active(cls, task_vars):  # pylint: disable=unused-argument
        """Returns true if this check applies to the ansible-playbook run."""
        return True

    @abstractmethod
    def run(self, tmp, task_vars):
        """Executes a check, normally implemented as a module."""
        return {}

    @classmethod
    def subclasses(cls):
        """Returns a generator of subclasses of this class and its subclasses."""
        for subclass in cls.__subclasses__():  # pylint: disable=no-member
            yield subclass
            for subclass in subclass.subclasses():
                yield subclass


# Dynamically import all submodules for the side effect of loading checks.

EXCLUDES = (
    "__init__.py",
    "mixins.py",
)

for name in os.listdir(os.path.dirname(__file__)):
    if name.endswith(".py") and name not in EXCLUDES:
        import_module(__package__ + "." + name[:-3])
