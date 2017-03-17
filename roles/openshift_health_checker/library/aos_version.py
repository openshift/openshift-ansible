#!/usr/bin/python
# vim: expandtab:tabstop=4:shiftwidth=4
'''
Ansible module for determining if multiple versions of an OpenShift package are
available, and if the version requested is available down to the given
precision.

Multiple versions available suggest that multiple repos are enabled for the
different versions, which may cause installation problems.
'''

import yum  # pylint: disable=import-error

from ansible.module_utils.basic import AnsibleModule


def main():  # pylint: disable=missing-docstring,too-many-branches
    module = AnsibleModule(
        argument_spec=dict(
            prefix=dict(required=True),  # atomic-openshift, origin, ...
            version=dict(required=True),
        ),
        supports_check_mode=True
    )

    def bail(error):  # pylint: disable=missing-docstring
        module.fail_json(msg=error)

    rpm_prefix = module.params['prefix']

    if not rpm_prefix:
        bail("prefix must not be empty")

    yb = yum.YumBase()  # pylint: disable=invalid-name
    yb.conf.disable_excludes = ["all"]  # assume the openshift excluder will be managed, ignore current state

    # search for package versions available for aos pkgs
    expected_pkgs = [
        rpm_prefix,
        rpm_prefix + '-master',
        rpm_prefix + '-node',
    ]
    try:
        pkgs = yb.pkgSack.returnPackages(patterns=expected_pkgs)
    except yum.Errors.PackageSackError as e:  # pylint: disable=invalid-name
        # you only hit this if *none* of the packages are available
        bail('Unable to find any OpenShift packages.\nCheck your subscription and repo settings.\n%s' % e)

    # determine what level of precision we're expecting for the version
    expected_version = module.params['version']
    if expected_version.startswith('v'):  # v3.3 => 3.3
        expected_version = expected_version[1:]
    num_dots = expected_version.count('.')

    pkgs_by_name_version = {}
    pkgs_precise_version_found = {}
    for pkg in pkgs:
        # get expected version precision
        match_version = '.'.join(pkg.version.split('.')[:num_dots + 1])
        if match_version == expected_version:
            pkgs_precise_version_found[pkg.name] = True
        # get x.y version precision
        minor_version = '.'.join(pkg.version.split('.')[:2])
        if pkg.name not in pkgs_by_name_version:
            pkgs_by_name_version[pkg.name] = {}
        pkgs_by_name_version[pkg.name][minor_version] = True

    # see if any packages couldn't be found at requested version
    # see if any packages are available in more than one minor version
    not_found = []
    multi_found = []
    for name in expected_pkgs:
        if name not in pkgs_precise_version_found:
            not_found.append(name)
        if name in pkgs_by_name_version and len(pkgs_by_name_version[name]) > 1:
            multi_found.append(name)
    if not_found:
        msg = 'Not all of the required packages are available at requested version %s:\n' % expected_version
        for name in not_found:
            msg += '  %s\n' % name
        bail(msg + 'Please check your subscriptions and enabled repositories.')
    if multi_found:
        msg = 'Multiple minor versions of these packages are available\n'
        for name in multi_found:
            msg += '  %s\n' % name
        bail(msg + "There should only be one OpenShift version's repository enabled at a time.")

    module.exit_json(changed=False)


if __name__ == '__main__':
    main()
