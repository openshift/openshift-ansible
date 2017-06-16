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
    """
    A base class for defining checks for an OpenShift cluster environment.

    Expect optional params: method execute_module, dict task_vars, and string tmp.
    execute_module is expected to have a signature compatible with _execute_module
    from ansible plugins/action/__init__.py, e.g.:
    def execute_module(module_name=None, module_args=None, tmp=None, task_vars=None, *args):
    This is stored so that it can be invoked in subclasses via check.execute_module("name", args)
    which provides the check's stored task_vars and tmp.
    """

    def __init__(self, execute_module=None, task_vars=None, tmp=None):
        self._execute_module = execute_module
        self.task_vars = task_vars or {}
        self.tmp = tmp

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

    @staticmethod
    def is_active():
        """Returns true if this check applies to the ansible-playbook run."""
        return True

    @abstractmethod
    def run(self):
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

    def execute_module(self, module_name=None, module_args=None):
        """Invoke an Ansible module from a check.

        Invoke stored _execute_module, normally copied from the action
        plugin, with its params and the task_vars and tmp given at
        check initialization. No positional parameters beyond these
        are specified. If it's necessary to specify any of the other
        parameters to _execute_module then that should just be invoked
        directly (with awareness of changes in method signature per
        Ansible version).

        So e.g. check.execute_module("foo", dict(arg1=...))
        Return: result hash from module execution.
        """
        if self._execute_module is None:
            raise NotImplementedError(
                self.__class__.__name__ +
                " invoked execute_module without providing the method at initialization."
            )
        return self._execute_module(module_name, module_args, self.tmp, self.task_vars)

    def get_var(self, *keys, **kwargs):
        """Get deeply nested values from task_vars.

        Ansible task_vars structures are Python dicts, often mapping strings to
        other dicts. This helper makes it easier to get a nested value, raising
        OpenShiftCheckException when a key is not found or returning a default value
        provided as a keyword argument.
        """
        try:
            value = reduce(operator.getitem, keys, self.task_vars)
        except (KeyError, TypeError):
            if "default" in kwargs:
                return kwargs["default"]
            raise OpenShiftCheckException("'{}' is undefined".format(".".join(map(str, keys))))
        return value


LOADER_EXCLUDES = (
    "__init__.py",
    "mixins.py",
    "logging.py",
)


def load_checks(path=None, subpkg=""):
    """Dynamically import all check modules for the side effect of registering checks."""
    if path is None:
        path = os.path.dirname(__file__)

    modules = []

    for name in os.listdir(path):
        if os.path.isdir(os.path.join(path, name)):
            modules = modules + load_checks(os.path.join(path, name), subpkg + "." + name)
            continue

        if name.endswith(".py") and name not in LOADER_EXCLUDES:
            modules.append(import_module(__package__ + subpkg + "." + name[:-3]))

    return modules
