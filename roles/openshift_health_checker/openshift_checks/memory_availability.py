# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, OpenShiftCheckException, get_var


class MemoryAvailability(OpenShiftCheck):
    """Check that recommended memory is available."""

    name = "memory_availability"
    tags = ["preflight"]

    recommended_memory_mb = {
        "nodes": 8 * 1000,
        "masters": 16 * 1000,
        "etcd": 10 * 1000,
    }

    @classmethod
    def is_active(cls, task_vars):
        """Skip hosts that do not have recommended memory space requirements."""
        group_names = get_var(task_vars, "group_names", default=[])
        has_mem_space_recommendation = bool(set(group_names).intersection(cls.recommended_memory_mb))
        return super(MemoryAvailability, cls).is_active(task_vars) and has_mem_space_recommendation

    def run(self, tmp, task_vars):
        group_names = get_var(task_vars, "group_names", default=[])
        total_memory = get_var(task_vars, "ansible_memtotal_mb")

        recommended_memory_mb = max(self.recommended_memory_mb.get(group, 0) for group in group_names)
        if not recommended_memory_mb:
            msg = "Unable to determine recommended memory size for group_name {group_name}"
            raise OpenShiftCheckException(msg.format(group_name=group_names))

        if total_memory < recommended_memory_mb:
            msg = ("Available memory ({available} MB) below recommended storage. "
                   "Minimum required memory: {recommended} MB")
            return {"failed": True, "msg": msg.format(available=total_memory, recommended=recommended_memory_mb)}

        return {"changed": False}
