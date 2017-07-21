"""A health check for OpenShift clusters."""

from openshift_checks import OpenShiftCheck, OpenShiftCheckException


class EtcdVolume(OpenShiftCheck):
    """Ensures etcd storage usage does not exceed a given threshold."""

    name = "etcd_volume"
    tags = ["etcd", "health"]

    # Default device usage threshold. Value should be in the range [0, 100].
    default_threshold_percent = 90
    # Where to find ectd data, higher priority first.
    supported_mount_paths = ["/var/lib/etcd", "/var/lib", "/var", "/"]

    def is_active(self):
        etcd_hosts = self.get_var("groups", "etcd", default=[]) or self.get_var("groups", "masters", default=[]) or []
        is_etcd_host = self.get_var("ansible_ssh_host") in etcd_hosts
        return super(EtcdVolume, self).is_active() and is_etcd_host

    def run(self):
        mount_info = self._etcd_mount_info()
        available = mount_info["size_available"]
        total = mount_info["size_total"]
        used = total - available

        threshold = self.get_var(
            "etcd_device_usage_threshold_percent",
            default=self.default_threshold_percent
        )

        used_percent = 100.0 * used / total

        if used_percent > threshold:
            device = mount_info.get("device", "unknown")
            mount = mount_info.get("mount", "unknown")
            msg = "etcd storage usage ({:.1f}%) is above threshold ({:.1f}%). Device: {}, mount: {}.".format(
                used_percent, threshold, device, mount
            )
            return {"failed": True, "msg": msg}

        return {}

    def _etcd_mount_info(self):
        ansible_mounts = self.get_var("ansible_mounts")
        mounts = {mnt.get("mount"): mnt for mnt in ansible_mounts}

        for path in self.supported_mount_paths:
            if path in mounts:
                return mounts[path]

        paths = ', '.join(sorted(mounts)) or 'none'
        msg = "Unable to find etcd storage mount point. Paths mounted: {}.".format(paths)
        raise OpenShiftCheckException(msg)
