"""
Health checks for OpenShift clusters.
"""

import operator
import os

from abc import ABCMeta, abstractmethod, abstractproperty
from importlib import import_module

from ansible.module_utils import six
from ansible.module_utils.six.moves import reduce  # pylint: disable=import-error,redefined-builtin


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

    @property
    def tags(self):
        """A list of tags that this check satisfy.

        Tags are used to reference multiple checks with a single '@tagname'
        special check name.
        """
        return []

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
        # AUDIT: no-member makes sense due to this having a metaclass
        for subclass in cls.__subclasses__():  # pylint: disable=no-member
            yield subclass
            for subclass in subclass.subclasses():
                yield subclass


def get_var(task_vars, *keys, **kwargs):
    """Helper function to get deeply nested values from task_vars.

    Ansible task_vars structures are Python dicts, often mapping strings to
    other dicts. This helper makes it easier to get a nested value, raising
    OpenShiftCheckException when a key is not found or returning a default value
    provided as a keyword argument.
    """
    try:
        value = reduce(operator.getitem, keys, task_vars)
    except (KeyError, TypeError):
        if "default" in kwargs:
            return kwargs["default"]
        raise OpenShiftCheckException("'{}' is undefined".format(".".join(map(str, keys))))
    return value


# Dynamically import all submodules for the side effect of loading checks.

EXCLUDES = (
    "__init__.py",
    "mixins.py",
)

for name in os.listdir(os.path.dirname(__file__)):
    if name.endswith(".py") and name not in EXCLUDES:
        import_module(__package__ + "." + name[:-3])
