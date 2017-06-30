# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, OpenShiftCheckException, get_var
from openshift_checks.mixins import NotContainerizedMixin


class DiskAvailability(NotContainerizedMixin, OpenShiftCheck):
    """Check that recommended disk space is available before a first-time install."""

    name = "disk_availability"
    tags = ["preflight"]

    # Values taken from the official installation documentation:
    # https://docs.openshift.org/latest/install_config/install/prerequisites.html#system-requirements
    recommended_disk_space_bytes = {
        "masters": 25 * 10**9,
        "nodes": 15 * 10**9,
        "etcd": 20 * 10**9,
    }

    @classmethod
    def is_active(cls, task_vars):
        """Skip hosts that do not have recommended disk space requirements."""
        group_names = get_var(task_vars, "group_names", default=[])
        has_disk_space_recommendation = bool(set(group_names).intersection(cls.recommended_disk_space_bytes))
        return super(DiskAvailability, cls).is_active(task_vars) and has_disk_space_recommendation

    def run(self, tmp, task_vars):
        group_names = get_var(task_vars, "group_names")
        ansible_mounts = get_var(task_vars, "ansible_mounts")
        free_bytes = self.openshift_available_disk(ansible_mounts)

        recommended_min = max(self.recommended_disk_space_bytes.get(name, 0) for name in group_names)
        configured_min = int(get_var(task_vars, "openshift_check_min_host_disk_gb", default=0)) * 10**9
        min_free_bytes = configured_min or recommended_min

        if free_bytes < min_free_bytes:
            return {
                'failed': True,
                'msg': (
                    'Available disk space ({:.1f} GB) for the volume containing '
                    '"/var" is below minimum recommended space ({:.1f} GB)'
                ).format(float(free_bytes) / 10**9, float(min_free_bytes) / 10**9)
            }

        return {}

    @staticmethod
    def openshift_available_disk(ansible_mounts):
        """Determine the available disk space for an OpenShift installation.

        ansible_mounts should be a list of dicts like the 'setup' Ansible module
        returns.
        """
        # priority list in descending order
        supported_mnt_paths = ["/var", "/"]
        available_mnts = {mnt.get("mount"): mnt for mnt in ansible_mounts}

        try:
            for path in supported_mnt_paths:
                if path in available_mnts:
                    return available_mnts[path]["size_available"]
        except KeyError:
            pass

        paths = ''.join(sorted(available_mnts)) or 'none'
        msg = "Unable to determine available disk space. Paths mounted: {}.".format(paths)
        raise OpenShiftCheckException(msg)
