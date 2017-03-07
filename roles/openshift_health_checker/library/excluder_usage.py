#!/usr/bin/python
# vim: expandtab:tabstop=4:shiftwidth=4
'''
Ansible module to test whether the openshift yum/RPM excluders are
present and as expected.

https://docs.openshift.com/container-platform/3.4/install_config/install/host_preparation.html#installing-base-packages

atomic-openshift-excluder and atomic-openshift-docker-excluder should be installed
and updated to the latest version that agrees with the version of OpenShift.
The docker excludes should always be on (excluded).
The openshift excludes may be on or off depending on the play. This module will not check it.

parameters:
  openshift_release: User-specified version of the desired version for OpenShift (typically x.y)
  rpm_prefix: (optional) package name prefix (origin vs atomic-openshift)
'''

import rpm, subprocess
from ansible.module_utils.basic import AnsibleModule


def main():
    module = AnsibleModule(
        argument_spec=dict(
            rpm_prefix=dict(default="atomic-openshift"),
            openshift_release=dict(required=True),
        ),
        supports_check_mode=True,
    )
    prefix=module.params['rpm_prefix']
    openshift_release=module.params['openshift_release']

    def bail(error):
        module.fail_json(msg=error)

    # test if excluder RPMs are installed and correct version
    ts = rpm.TransactionSet()
    #yb = yum.YumBase()
    errors = ""
    version = {}
    for pkg in [prefix+"-excluder", prefix+"-docker-excluder"]:
        matches = ts.dbMatch("name", pkg)
        for header in matches:
            version[pkg] = header["version"]
            # test if the RPMs match the version of OpenShift we're expecting
            if not version[pkg].startswith(openshift_release):
                errors = errors + ('Installed package %s version %s does not match requested OpenShift version %s. Please install a matching package version.\n'
                         % (pkg, version[pkg], openshift_release))
        if version.has_key(pkg):
            # TODO: test if the RPMs have an update
            pass
        else:
            errors = errors + pkg + ' package is not installed. Please install this package.\n'
    if len(errors) > 0: bail(errors)

    # test if docker-excluder status returns non-zero
    return_code = subprocess.call([prefix+"-docker-excluder", "status"])
    if return_code != 0:
        bail(prefix+"-docker-excluder does not appear to be enabled. This should always be enabled:\n"
                + prefix+"-docker-excluder exclude" )

    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
