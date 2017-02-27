# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, OpenShiftCheckException, get_var
from openshift_checks.mixins import NotContainerizedMixin


class DiskAvailability(NotContainerizedMixin, OpenShiftCheck):
    """Check that recommended disk space is available before a first-time install."""

    name = "disk_availability"
    tags = ["preflight"]

    # all values are base-10 as they are taken, as is, from
    # the latest requirements for an OpenShift installation
    # https://docs.openshift.org/latest/install_config/install/prerequisites.html#system-requirements
    recommended_diskspace = {
        "nodes": 15 * 10 ** 9,
        "masters": 40 * 10 ** 9,
        "etcd": 20 * 10 ** 9,
    }

    def run(self, tmp, task_vars):
        ansible_mounts = get_var(task_vars, "ansible_mounts")
        self.recommended_diskspace["nodes"] = get_var(task_vars,
                                                      "min_recommended_diskspace_node",
                                                      default=self.recommended_diskspace["nodes"])
        self.recommended_diskspace["masters"] = get_var(task_vars,
                                                        "min_recommended_diskspace_master",
                                                        default=self.recommended_diskspace["masters"])
        self.recommended_diskspace["etcd"] = get_var(task_vars,
                                                     "min_recommended_diskspace_etcd",
                                                     default=self.recommended_diskspace["etcd"])

        failed, msg = self.volume_check(ansible_mounts, task_vars)
        return {"failed": failed, "msg": msg}

    def volume_check(self, ansible_mounts, task_vars):
        group_names = get_var(task_vars, "group_names", default=[])

        if not set(self.recommended_diskspace).intersection(group_names):
            msg = "Unable to determine recommended volume size for group_name {group_name}"
            raise OpenShiftCheckException(msg.format(group_name=group_names))

        recommended_diskspace_bytes = max(self.recommended_diskspace.get(group, 0) for group in group_names)
        openshift_diskfree_bytes = self.get_openshift_disk_availability(ansible_mounts)

        if openshift_diskfree_bytes < recommended_diskspace_bytes:
            msg = ("Available disk space ({diskfree} GB) for the volume containing \"/var\" is "
                   "below recommended storage. Minimum required disk space: {recommended} GB")
            return True, msg.format(diskfree=self.to_gigabytes(openshift_diskfree_bytes),
                                    recommended=self.to_gigabytes(recommended_diskspace_bytes))

        return False, ""

    @staticmethod
    def get_openshift_disk_availability(ansible_mounts):
        """Iterates through a map of mounted volumes to determine space remaining on the OpenShift volume"""
        if not ansible_mounts:
            msg = "Unable to determine existing volume mounts from ansible_mounts"
            raise OpenShiftCheckException(msg)

        # priority list in descending order
        supported_mnt_paths = ["/var", "/"]
        available_mnts = {mnt.get("mount"): mnt for mnt in ansible_mounts}

        for path in supported_mnt_paths:
            if path in available_mnts:
                return available_mnts[path].get("size_available")

        return 0

    @staticmethod
    def to_gigabytes(total_bytes):
        return total_bytes / 10**9
