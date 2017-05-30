"""Check that scans journalctl for messages caused as a symptom of increased etcd traffic."""

from openshift_checks import OpenShiftCheck, get_var


class EtcdTraffic(OpenShiftCheck):
    """Check if host is being affected by an increase in etcd traffic."""

    name = "etcd_traffic"
    tags = ["health", "etcd"]

    @classmethod
    def is_active(cls, task_vars):
        """Skip hosts that do not have etcd in their group names."""
        group_names = get_var(task_vars, "group_names", default=[])
        valid_group_names = "etcd" in group_names

        version = get_var(task_vars, "openshift", "common", "short_version")
        valid_version = version in ("3.4", "3.5", "1.4", "1.5")

        return super(EtcdTraffic, cls).is_active(task_vars) and valid_group_names and valid_version

    def run(self, tmp, task_vars):
        is_containerized = get_var(task_vars, "openshift", "common", "is_containerized")
        unit = "etcd_container" if is_containerized else "etcd"

        log_matchers = [{
            "start_regexp": r"Starting Etcd Server",
            "regexp": r"etcd: sync duration of [^,]+, expected less than 1s",
            "unit": unit
        }]

        match = self.execute_module("search_journalctl", {
            "log_matchers": log_matchers,
        }, task_vars)

        if match.get("matched"):
            msg = ("Higher than normal etcd traffic detected.\n"
                   "OpenShift 3.4 introduced an increase in etcd traffic.\n"
                   "Upgrading to OpenShift 3.6 is recommended in order to fix this issue.\n"
                   "Please refer to https://access.redhat.com/solutions/2916381 for more information.")
            return {"failed": True, "msg": msg}

        if match.get("failed"):
            return {"failed": True, "msg": "\n".join(match.get("errors"))}

        return {}
