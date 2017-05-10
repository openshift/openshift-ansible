"""
Ansible module for warning about etcd volume size past a defined threshold.
"""

from openshift_checks import OpenShiftCheck, OpenShiftCheckException, get_var


class EtcdVolume(OpenShiftCheck):
    """Ensure disk size for an etcd host does not exceed a defined limit"""

    name = "etcd_volume"
    tags = ["etcd", "health"]

    etcd_default_size_limit_percent = 0.9

    def run(self, tmp, task_vars):
        ansible_mounts = get_var(task_vars, "ansible_mounts")

        etcd_mount_path = self._get_etcd_mount_path(ansible_mounts)
        etcd_disk_size_available = float(etcd_mount_path["size_available"])
        etcd_disk_size_total = float(etcd_mount_path["size_total"])
        etcd_disk_size_used = etcd_disk_size_total - etcd_disk_size_available

        size_limit_percent = get_var(
            task_vars,
            "etcd_disk_size_limit_percent",
            default=self.etcd_default_size_limit_percent
        )

        if etcd_disk_size_used / etcd_disk_size_total > size_limit_percent:
            msg = ("Current etcd volume usage ({actual:.2f} GB) for the volume \"{volume}\" "
                   "is greater than the storage limit ({limit:.2f} GB).")
            msg = msg.format(
                actual=self._to_gigabytes(etcd_disk_size_used),
                volume=etcd_mount_path["mount"],
                limit=self._to_gigabytes(size_limit_percent * etcd_disk_size_total),
            )
            return {"failed": True, "msg": msg}

        return {"changed": False}

    @staticmethod
    def _get_etcd_mount_path(ansible_mounts):
        supported_mnt_paths = ["/var/lib/etcd", "/var/lib", "/var", "/"]
        available_mnts = {mnt.get("mount"): mnt for mnt in ansible_mounts}

        for path in supported_mnt_paths:
            if path in available_mnts:
                return available_mnts[path]

        paths = ', '.join(sorted(available_mnts)) or 'none'
        msg = "Unable to determine available disk space. Paths mounted: {}.".format(paths)
        raise OpenShiftCheckException(msg)

    @staticmethod
    def _to_gigabytes(byte_size):
        return float(byte_size) / 10.0**9
