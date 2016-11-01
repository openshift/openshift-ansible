"""
Defines the supported variants and versions the installer supports, and metadata
required to run Ansible correctly.

This module needs to be updated for each major release to allow the new version
to be specified by the user, and to point the generic variants to the latest
version.
"""


# pylint: disable=too-few-public-methods
class Version(object):
    """
    Defines a deploy_type for use by the ansible playbooks.

    Attributes:
        name (str): The major and minor version for the deployment type.mro
                    e.g. 3.0, 3.1
        ansible_key (str): What will become deployment_type in the ansible inventory
        subtype (str): A marker for disabling features or running additional
                       configuration for a deployment.
    """
    def __init__(self, name, ansible_key, subtype=''):
        self.name = name

        self.ansible_key = ansible_key
        self.subtype = subtype


class Variant(object):
    """
    A wrapper for similar Versions

    Attributes:
        name (str): Supported variant name.
        description (str): A friendly name for the variant.
        versions (list): A collection of Versions. In order for this to
                         function correctly, the Versions must be ordered
                         from newest to oldest.
    """
    def __init__(self, name, description, versions):
        self.name = name
        self.description = description
        self.versions = versions

    def latest_version(self):
        """
        Returns the first entry in the versions collection, which
        if it is properly ordered, should be the newest.
        """
        return self.versions[0]


# WARNING: Keep the versions ordered, most recent first:
OSE = Variant('openshift-enterprise', 'OpenShift Container Platform',
              [
                  Version('3.4', 'openshift-enterprise'),
              ]
             )

REG = Variant('openshift-enterprise', 'Registry',
              [
                  Version('3.4', 'openshift-enterprise', 'registry'),
              ]
             )

ORIGIN = Variant('origin', 'OpenShift Origin',
                 [
                     Version('1.4', 'origin'),
                 ]
                )

LEGACY = Variant('openshift-enterprise', 'OpenShift Container Platform',
                 [
                     Version('3.3', 'openshift-enterprise'),
                     Version('3.2', 'openshift-enterprise'),
                     Version('3.1', 'openshift-enterprise'),
                     Version('3.0', 'openshift-enterprise'),
                 ]
                )

# Ordered list of variants we can install, first is the default.
SUPPORTED_VARIANTS = (OSE, REG, ORIGIN, LEGACY)
DISPLAY_VARIANTS = (OSE, REG,)


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
            for ver in prod.versions:
                if ver.name == version:
                    return (prod, ver)

    return (None, None)


def get_variant_version_combos():
    """
    Returns a list of Variants to display to the user in
    interactive mode.
    """
    combos = []
    for variant in DISPLAY_VARIANTS:
        for ver in variant.versions:
            combos.append((variant, ver))
    return combos
