# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, OpenShiftCheckException
from openshift_checks.mixins import NotContainerized


class PackageAvailability(NotContainerized, OpenShiftCheck):
    """Check that required RPM packages are available."""

    name = "package_availability"

    def run(self, tmp, task_vars):
        try:
            rpm_prefix = task_vars["openshift"]["common"]["service_type"]
        except (KeyError, TypeError):
            raise OpenShiftCheckException("'openshift.common.service_type' is undefined")

        group_names = task_vars.get("group_names", [])

        packages = set()

        if "masters" in group_names:
            packages.update(self.master_packages(rpm_prefix))
        if "nodes" in group_names:
            packages.update(self.node_packages(rpm_prefix))

        args = {"packages": sorted(set(packages))}
        return self.module_executor("check_yum_update", args, tmp, task_vars)

    @staticmethod
    def master_packages(rpm_prefix):
        return [
            "{rpm_prefix}".format(rpm_prefix=rpm_prefix),
            "{rpm_prefix}-clients".format(rpm_prefix=rpm_prefix),
            "{rpm_prefix}-master".format(rpm_prefix=rpm_prefix),
            "bash-completion",
            "cockpit-bridge",
            "cockpit-docker",
            "cockpit-kubernetes",
            "cockpit-shell",
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
