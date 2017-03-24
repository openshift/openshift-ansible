# pylint: disable=missing-docstring
from openshift_checks import OpenShiftCheck, get_var


class DockerStorageDriver(OpenShiftCheck):
    """Check Docker storage driver compatibility.

    This check ensures that Docker is using a supported storage driver,
    and that Loopback is not being used (if using devicemapper).
    """

    name = "docker_storage_driver"
    tags = ["preflight"]

    storage_drivers = ["devicemapper", "overlay2"]

    @classmethod
    def is_active(cls, task_vars):
        """Skip non-containerized installations."""
        is_containerized = get_var(task_vars, "openshift", "common", "is_containerized")
        return super(DockerStorageDriver, cls).is_active(task_vars) and is_containerized

    def run(self, tmp, task_vars):
        info = self.execute_module("docker_info", {}, task_vars).get("info", {})

        if not self.is_supported_storage_driver(info):
            msg = "Unsupported Docker storage driver detected. Supported storage drivers: {drivers}"
            return {"failed": True, "msg": msg.format(drivers=', '.join(self.storage_drivers))}

        if self.is_using_loopback_device(info):
            msg = "Use of loopback devices is discouraged. Try running Docker with `--storage-opt dm.thinpooldev`"
            return {"failed": True, "msg": msg}

        return {}

    def is_supported_storage_driver(self, docker_info):
        return docker_info.get("Driver", "") in self.storage_drivers

    @staticmethod
    def is_using_loopback_device(docker_info):
        # Loopback device usage is only an issue if using devicemapper.
        # Skip this check if using any other storage driver.
        if docker_info.get("Driver", "") != "devicemapper":
            return False

        for status in docker_info.get("DriverStatus", []):
            if status[0] == "Data loop file":
                return bool(status[1])

        return False
