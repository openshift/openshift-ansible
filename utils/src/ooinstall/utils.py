# pylint: disable=missing-docstring,invalid-name

import logging
import re


installer_log = logging.getLogger('installer')


def debug_env(env):
    for k in sorted(env.keys()):
        if k.startswith("OPENSHIFT") or k.startswith("ANSIBLE") or k.startswith("OO"):
            # pylint: disable=logging-format-interpolation
            installer_log.debug("{key}: {value}".format(
                key=k, value=env[k]))


def is_valid_hostname(hostname):
    if not hostname or len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1]  # strip exactly one dot from the right, if present
    allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))
