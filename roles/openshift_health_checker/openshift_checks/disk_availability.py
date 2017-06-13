"""Check that there is enough disk space in predefined paths."""

import os.path
import tempfile

from openshift_checks import OpenShiftCheck, OpenShiftCheckException, get_var


class DiskAvailability(OpenShiftCheck):
    """Check that recommended disk space is available before a first-time install."""

    name = "disk_availability"
    tags = ["preflight"]

    # Values taken from the official installation documentation:
    # https://docs.openshift.org/latest/install_config/install/prerequisites.html#system-requirements
    recommended_disk_space_bytes = {
        '/var': {
            'masters': 40 * 10**9,
            'nodes': 15 * 10**9,
            'etcd': 20 * 10**9,
        },
        # Used to copy client binaries into,
        # see roles/openshift_cli/library/openshift_container_binary_sync.py.
        '/usr/local/bin': {
            'masters': 1 * 10**9,
            'nodes': 1 * 10**9,
            'etcd': 1 * 10**9,
        },
        # Used as temporary storage in several cases.
        tempfile.gettempdir(): {
            'masters': 1 * 10**9,
            'nodes': 1 * 10**9,
            'etcd': 1 * 10**9,
        },
    }

    @classmethod
    def is_active(cls, task_vars):
        """Skip hosts that do not have recommended disk space requirements."""
        group_names = get_var(task_vars, "group_names", default=[])
        active_groups = set()
        for recommendation in cls.recommended_disk_space_bytes.values():
            active_groups.update(recommendation.keys())
        has_disk_space_recommendation = bool(active_groups.intersection(group_names))
        return super(DiskAvailability, cls).is_active(task_vars) and has_disk_space_recommendation

    def run(self, tmp, task_vars):
        group_names = get_var(task_vars, "group_names")
        ansible_mounts = get_var(task_vars, "ansible_mounts")
        ansible_mounts = {mount['mount']: mount for mount in ansible_mounts}

        user_config = get_var(task_vars, "openshift_check_min_host_disk_gb", default={})
        try:
            # For backwards-compatibility, if openshift_check_min_host_disk_gb
            # is a number, then it overrides the required config for '/var'.
            number = float(user_config)
            user_config = {
                '/var': {
                    'masters': number,
                    'nodes': number,
                    'etcd': number,
                },
            }
        except TypeError:
            # If it is not a number, then it should be a nested dict.
            pass

        # TODO: as suggested in
        # https://github.com/openshift/openshift-ansible/pull/4436#discussion_r122180021,
        # maybe we could support checking disk availability in paths that are
        # not part of the official recommendation but present in the user
        # configuration.
        for path, recommendation in self.recommended_disk_space_bytes.items():
            free_bytes = self.free_bytes(path, ansible_mounts)
            recommended_bytes = max(recommendation.get(name, 0) for name in group_names)

            config = user_config.get(path, {})
            # NOTE: the user config is in GB, but we compare bytes, thus the
            # conversion.
            config_bytes = max(config.get(name, 0) for name in group_names) * 10**9
            recommended_bytes = config_bytes or recommended_bytes

            if free_bytes < recommended_bytes:
                free_gb = float(free_bytes) / 10**9
                recommended_gb = float(recommended_bytes) / 10**9
                return {
                    'failed': True,
                    'msg': (
                        'Available disk space in "{}" ({:.1f} GB) '
                        'is below minimum recommended ({:.1f} GB)'
                    ).format(path, free_gb, recommended_gb)
                }

        return {}

    @staticmethod
    def free_bytes(path, ansible_mounts):
        """Return the size available in path based on ansible_mounts."""
        mount_point = path
        # arbitry value to prevent an infinite loop, in the unlike case that '/'
        # is not in ansible_mounts.
        max_depth = 32
        while mount_point not in ansible_mounts and max_depth > 0:
            mount_point = os.path.dirname(mount_point)
            max_depth -= 1

        try:
            free_bytes = ansible_mounts[mount_point]['size_available']
        except KeyError:
            known_mounts = ', '.join('"{}"'.format(mount) for mount in sorted(ansible_mounts)) or 'none'
            msg = 'Unable to determine disk availability for "{}". Known mount points: {}.'
            raise OpenShiftCheckException(msg.format(path, known_mounts))

        return free_bytes
