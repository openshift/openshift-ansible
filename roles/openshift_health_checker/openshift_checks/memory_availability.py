# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, get_var


class MemoryAvailability(OpenShiftCheck):
    """Check that recommended memory is available."""

    name = "memory_availability"
    tags = ["preflight"]

    # Values taken from the official installation documentation:
    # https://docs.openshift.org/latest/install_config/install/prerequisites.html#system-requirements
    recommended_memory_bytes = {
        "masters": 16 * 10**9,
        "nodes": 8 * 10**9,
        "etcd": 20 * 10**9,
    }

    @classmethod
    def is_active(cls, task_vars):
        """Skip hosts that do not have recommended memory requirements."""
        group_names = get_var(task_vars, "group_names", default=[])
        has_memory_recommendation = bool(set(group_names).intersection(cls.recommended_memory_bytes))
        return super(MemoryAvailability, cls).is_active(task_vars) and has_memory_recommendation

    def run(self, tmp, task_vars):
        group_names = get_var(task_vars, "group_names")
        total_memory_bytes = get_var(task_vars, "ansible_memtotal_mb") * 10**6

        min_memory_bytes = max(self.recommended_memory_bytes.get(name, 0) for name in group_names)

        if total_memory_bytes < min_memory_bytes:
            return {
                'failed': True,
                'msg': (
                    'Available memory ({available:.1f} GB) '
                    'below recommended value ({recommended:.1f} GB)'
                ).format(
                    available=float(total_memory_bytes) / 10**9,
                    recommended=float(min_memory_bytes) / 10**9,
                ),
            }

        return {}
