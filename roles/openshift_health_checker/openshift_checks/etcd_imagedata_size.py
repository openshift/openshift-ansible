"""
Ansible module for determining if the size of OpenShift image data exceeds a specified limit in an etcd cluster.
"""

from openshift_checks import OpenShiftCheck, OpenShiftCheckException, get_var


class EtcdImageDataSize(OpenShiftCheck):
    """Check that total size of OpenShift image data does not exceed the recommended limit in an etcd cluster"""

    name = "etcd_imagedata_size"
    tags = ["etcd"]

    def run(self, tmp, task_vars):
        etcd_mountpath = self._get_etcd_mountpath(get_var(task_vars, "ansible_mounts"))
        etcd_avail_diskspace = etcd_mountpath["size_available"]
        etcd_total_diskspace = etcd_mountpath["size_total"]

        etcd_imagedata_size_limit = get_var(task_vars,
                                            "etcd_max_image_data_size_bytes",
                                            default=int(0.5 * float(etcd_total_diskspace - etcd_avail_diskspace)))

        etcd_is_ssl = get_var(task_vars, "openshift", "master", "etcd_use_ssl", default=False)
        etcd_port = get_var(task_vars, "openshift", "master", "etcd_port", default=2379)
        etcd_hosts = get_var(task_vars, "openshift", "master", "etcd_hosts")

        config_base = get_var(task_vars, "openshift", "common", "config_base")

        cert = task_vars.get("etcd_client_cert", config_base + "/master/master.etcd-client.crt")
        key = task_vars.get("etcd_client_key", config_base + "/master/master.etcd-client.key")
        ca_cert = task_vars.get("etcd_client_ca_cert", config_base + "/master/master.etcd-ca.crt")

        for etcd_host in list(etcd_hosts):
            args = {
                "size_limit_bytes": etcd_imagedata_size_limit,
                "paths": ["/openshift.io/images", "/openshift.io/imagestreams"],
                "host": etcd_host,
                "port": etcd_port,
                "protocol": "https" if etcd_is_ssl else "http",
                "version_prefix": "/v2",
                "allow_redirect": True,
                "ca_cert": ca_cert,
                "cert": {
                    "cert": cert,
                    "key": key,
                },
            }

            etcdkeysize = self.module_executor("etcdkeysize", args, task_vars)

            if etcdkeysize.get("rc", 0) != 0 or etcdkeysize.get("failed"):
                msg = 'Failed to retrieve stats for etcd host "{host}": {reason}'
                reason = etcdkeysize.get("msg")
                if etcdkeysize.get("module_stderr"):
                    reason = etcdkeysize["module_stderr"]

                msg = msg.format(host=etcd_host, reason=reason)
                return {"failed": True, "changed": False, "msg": msg}

            if etcdkeysize["size_limit_exceeded"]:
                limit = self._to_gigabytes(etcd_imagedata_size_limit)
                msg = ("The size of OpenShift image data stored in etcd host "
                       "\"{host}\" exceeds the maximum recommended limit of {limit:.2f} GB. "
                       "Use the `oadm prune images` command to cleanup unused Docker images.")
                return {"failed": True, "msg": msg.format(host=etcd_host, limit=limit)}

        return {"changed": False}

    @staticmethod
    def _get_etcd_mountpath(ansible_mounts):
        valid_etcd_mount_paths = ["/var/lib/etcd", "/var/lib", "/var", "/"]

        mount_for_path = {mnt.get("mount"): mnt for mnt in ansible_mounts}
        for path in valid_etcd_mount_paths:
            if path in mount_for_path:
                return mount_for_path[path]

        paths = ', '.join(sorted(mount_for_path)) or 'none'
        msg = "Unable to determine a valid etcd mountpath. Paths mounted: {}.".format(paths)
        raise OpenShiftCheckException(msg)

    @staticmethod
    def _to_gigabytes(byte_size):
        return float(byte_size) / 10.0**9
