"""
Defines the supported variants and versions the installer supports, and metadata
required to run Ansible correctly.

This module needs to be updated for each major release to allow the new version
to be specified by the user, and to point the generic variants to the latest
version.
"""


class Version(object):
    def __init__(self, name, ansible_key):
        self.name = name  # i.e. 3.0, 3.1

        self.ansible_key = ansible_key


class Variant(object):
    def __init__(self, name, description, versions):
        # Supported variant name:
        self.name = name

        # Friendly name for the variant:
        self.description = description

        self.versions = versions


# WARNING: Keep the versions ordered, most recent last:
OSE = Variant('openshift-enterprise', 'OpenShift Enterprise',
    [
        Version('3.0', 'enterprise'),
        Version('3.1', 'openshift-enterprise')
    ]
)

AEP = Variant('atomic-enterprise', 'Atomic OpenShift Enterprise',
    [
        Version('3.1', 'atomic-enterprise')
    ]
)

# Ordered list of variants we can install, first is the default.
SUPPORTED_VARIANTS = (OSE, AEP)


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
                return (prod, prod.versions[-1])
            for v in prod.versions:
                if v.name == version:
                    return (prod, v)

    return (None, None)

def get_variant_version_combos():
    combos = []
    for variant in SUPPORTED_VARIANTS:
        for ver in variant.versions:
            combos.append((variant, ver))
    return combos

