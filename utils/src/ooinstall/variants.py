# TODO: Temporarily disabled due to importing old code into openshift-ansible
# repo. We will work on these over time.
# pylint: disable=bad-continuation,missing-docstring,no-self-use,invalid-name,too-few-public-methods

"""
Defines the supported variants and versions the installer supports, and metadata
required to run Ansible correctly.

This module needs to be updated for each major release to allow the new version
to be specified by the user, and to point the generic variants to the latest
version.
"""

import logging
installer_log = logging.getLogger('installer')


class Version(object):
    def __init__(self, name, ansible_key, subtype=''):
        self.name = name  # i.e. 3.0, 3.1

        self.ansible_key = ansible_key
        self.subtype = subtype


class Variant(object):
    def __init__(self, name, description, versions):
        # Supported variant name:
        self.name = name

        # Friendly name for the variant:
        self.description = description

        self.versions = versions

    def latest_version(self):
        return self.versions[0]


# WARNING: Keep the versions ordered, most recent first:
OSE = Variant('openshift-enterprise', 'OpenShift Container Platform', [
    Version('3.6', 'openshift-enterprise'),
])

REG = Variant('openshift-enterprise', 'Registry', [
    Version('3.6', 'openshift-enterprise', 'registry'),
])

origin = Variant('origin', 'OpenShift Origin', [
    Version('3.6', 'origin'),
])

LEGACY = Variant('openshift-enterprise', 'OpenShift Container Platform', [
    Version('3.5', 'openshift-enterprise'),
    Version('3.4', 'openshift-enterprise'),
    Version('3.3', 'openshift-enterprise'),
    Version('3.2', 'openshift-enterprise'),
    Version('3.1', 'openshift-enterprise'),
    Version('3.0', 'openshift-enterprise'),
])

# Ordered list of variants we can install, first is the default.
SUPPORTED_VARIANTS = (OSE, REG, origin, LEGACY)
DISPLAY_VARIANTS = (OSE, REG, origin)


def find_variant(name, version=None):
    """
    Locate the variant object for the variant given in config file, and
    the correct version to use for it.
    Return (None, None) if we can't find a match.
    """
    prod = None
    for prod in SUPPORTED_VARIANTS:
        if prod.name == name:
            if version is None:
                return (prod, prod.latest_version())
            for v in prod.versions:
                if v.name == version:
                    return (prod, v)

    return (None, None)


def get_variant_version_combos():
    combos = []
    for variant in DISPLAY_VARIANTS:
        for ver in variant.versions:
            combos.append((variant, ver))
    return combos
