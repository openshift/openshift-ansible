# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, get_var
from openshift_checks.mixins import NotContainerizedMixin


class PackageAvailability(NotContainerizedMixin, OpenShiftCheck):
    """Check that required RPM packages are available."""

    name = "package_availability"
    tags = ["preflight"]

    @classmethod
    def is_active(cls, task_vars):
        return super(PackageAvailability, cls).is_active(task_vars) and task_vars["ansible_pkg_mgr"] == "yum"

    def run(self, tmp, task_vars):
        rpm_prefix = get_var(task_vars, "openshift", "common", "service_type")
        group_names = get_var(task_vars, "group_names", default=[])

        packages = set()

        if "masters" in group_names:
            packages.update(self.master_packages(rpm_prefix))
        if "nodes" in group_names:
            packages.update(self.node_packages(rpm_prefix))

        args = {"packages": sorted(set(packages))}
        return self.execute_module("check_yum_update", args, tmp=tmp, task_vars=task_vars)

    @staticmethod
    def master_packages(rpm_prefix):
        return [
            "{rpm_prefix}".format(rpm_prefix=rpm_prefix),
            "{rpm_prefix}-clients".format(rpm_prefix=rpm_prefix),
            "{rpm_prefix}-master".format(rpm_prefix=rpm_prefix),
            "bash-completion",
            "cockpit-bridge",
            "cockpit-docker",
            "cockpit-system",
            "cockpit-ws",
            "etcd",
            "httpd-tools",
        ]

    @staticmethod
    def node_packages(rpm_prefix):
        return [
            "{rpm_prefix}".format(rpm_prefix=rpm_prefix),
            "{rpm_prefix}-node".format(rpm_prefix=rpm_prefix),
            "{rpm_prefix}-sdn-ovs".format(rpm_prefix=rpm_prefix),
            "bind",
            "ceph-common",
            "dnsmasq",
            "docker",
            "firewalld",
            "flannel",
            "glusterfs-fuse",
            "iptables-services",
            "iptables",
            "iscsi-initiator-utils",
            "libselinux-python",
            "nfs-utils",
            "ntp",
            "openssl",
            "pyparted",
            "python-httplib2",
            "PyYAML",
            "yum-utils",
        ]
