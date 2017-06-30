"""Check Docker storage driver and usage."""
import json
import re
from openshift_checks import OpenShiftCheck, OpenShiftCheckException, get_var
from openshift_checks.mixins import DockerHostMixin


class DockerStorage(DockerHostMixin, OpenShiftCheck):
    """Check Docker storage driver compatibility.

    This check ensures that Docker is using a supported storage driver,
    and that loopback is not being used (if using devicemapper).
    Also that storage usage is not above threshold.
    """

    name = "docker_storage"
    tags = ["pre-install", "health", "preflight"]

    dependencies = ["python-docker-py"]
    storage_drivers = ["devicemapper", "overlay2"]
    max_thinpool_data_usage_percent = 90.0
    max_thinpool_meta_usage_percent = 90.0

    # pylint: disable=too-many-return-statements
    # Reason: permanent stylistic exception;
    #         it is clearer to return on failures and there are just many ways to fail here.
    def run(self, tmp, task_vars):
        msg, failed, changed = self.ensure_dependencies(task_vars)
        if failed:
            return {
                "failed": True,
                "changed": changed,
                "msg": "Some dependencies are required in order to query docker storage on host:\n" + msg
            }

        # attempt to get the docker info hash from the API
        info = self.execute_module("docker_info", {}, task_vars=task_vars)
        if info.get("failed"):
            return {"failed": True, "changed": changed,
                    "msg": "Failed to query Docker API. Is docker running on this host?"}
        if not info.get("info"):  # this would be very strange
            return {"failed": True, "changed": changed,
                    "msg": "Docker API query missing info:\n{}".format(json.dumps(info))}
        info = info["info"]

        # check if the storage driver we saw is valid
        driver = info.get("Driver", "[NONE]")
        if driver not in self.storage_drivers:
            msg = (
                "Detected unsupported Docker storage driver '{driver}'.\n"
                "Supported storage drivers are: {drivers}"
            ).format(driver=driver, drivers=', '.join(self.storage_drivers))
            return {"failed": True, "changed": changed, "msg": msg}

        # driver status info is a list of tuples; convert to dict and validate based on driver
        driver_status = {item[0]: item[1] for item in info.get("DriverStatus", [])}
        if driver == "devicemapper":
            if driver_status.get("Data loop file"):
                msg = (
                    "Use of loopback devices with the Docker devicemapper storage driver\n"
                    "(the default storage configuration) is unsupported in production.\n"
                    "Please use docker-storage-setup to configure a backing storage volume.\n"
                    "See http://red.ht/2rNperO for further information."
                )
                return {"failed": True, "changed": changed, "msg": msg}
            result = self._check_dm_usage(driver_status, task_vars)
            result['changed'] = result.get('changed', False) or changed
            return result

        # TODO(lmeyer): determine how to check usage for overlay2

        return {"changed": changed}

    def _check_dm_usage(self, driver_status, task_vars):
        """
        Backing assumptions: We expect devicemapper to be backed by an auto-expanding thin pool
        implemented as an LV in an LVM2 VG. This is how docker-storage-setup currently configures
        devicemapper storage. The LV is "thin" because it does not use all available storage
        from its VG, instead expanding as needed; so to determine available space, we gather
        current usage as the Docker API reports for the driver as well as space available for
        expansion in the pool's VG.
        Usage within the LV is divided into pools allocated to data and metadata, either of which
        could run out of space first; so we check both.
        """
        vals = dict(
            vg_free=self._get_vg_free(driver_status.get("Pool Name"), task_vars),
            data_used=driver_status.get("Data Space Used"),
            data_total=driver_status.get("Data Space Total"),
            metadata_used=driver_status.get("Metadata Space Used"),
            metadata_total=driver_status.get("Metadata Space Total"),
        )

        # convert all human-readable strings to bytes
        for key, value in vals.copy().items():
            try:
                vals[key + "_bytes"] = self._convert_to_bytes(value)
            except ValueError as err:  # unlikely to hit this from API info, but just to be safe
                return {
                    "failed": True,
                    "values": vals,
                    "msg": "Could not interpret {} value '{}' as bytes: {}".format(key, value, str(err))
                }

        # determine the threshold percentages which usage should not exceed
        for name, default in [("data", self.max_thinpool_data_usage_percent),
                              ("metadata", self.max_thinpool_meta_usage_percent)]:
            percent = get_var(task_vars, "max_thinpool_" + name + "_usage_percent", default=default)
            try:
                vals[name + "_threshold"] = float(percent)
            except ValueError:
                return {
                    "failed": True,
                    "msg": "Specified thinpool {} usage limit '{}' is not a percentage".format(name, percent)
                }

        # test whether the thresholds are exceeded
        messages = []
        for name in ["data", "metadata"]:
            vals[name + "_pct_used"] = 100 * vals[name + "_used_bytes"] / (
                vals[name + "_total_bytes"] + vals["vg_free_bytes"])
            if vals[name + "_pct_used"] > vals[name + "_threshold"]:
                messages.append(
                    "Docker thinpool {name} usage percentage {pct:.1f} "
                    "is higher than threshold {thresh:.1f}.".format(
                        name=name,
                        pct=vals[name + "_pct_used"],
                        thresh=vals[name + "_threshold"],
                    ))
                vals["failed"] = True

        vals["msg"] = "\n".join(messages or ["Thinpool usage is within thresholds."])
        return vals

    def _get_vg_free(self, pool, task_vars):
        # Determine which VG to examine according to the pool name, the only indicator currently
        # available from the Docker API driver info. We assume a name that looks like
        # "vg--name-docker--pool"; vg and lv names with inner hyphens doubled, joined by a hyphen.
        match = re.match(r'((?:[^-]|--)+)-(?!-)', pool)  # matches up to the first single hyphen
        if not match:  # unlikely, but... be clear if we assumed wrong
            raise OpenShiftCheckException(
                "This host's Docker reports it is using a storage pool named '{}'.\n"
                "However this name does not have the expected format of 'vgname-lvname'\n"
                "so the available storage in the VG cannot be determined.".format(pool)
            )
        vg_name = match.groups()[0].replace("--", "-")
        vgs_cmd = "/sbin/vgs --noheadings -o vg_free --units g --select vg_name=" + vg_name
        # should return free space like "  12.00g" if the VG exists; empty if it does not

        ret = self.execute_module("command", {"_raw_params": vgs_cmd}, task_vars=task_vars)
        if ret.get("failed") or ret.get("rc", 0) != 0:
            raise OpenShiftCheckException(
                "Is LVM installed? Failed to run /sbin/vgs "
                "to determine docker storage usage:\n" + ret.get("msg", "")
            )
        size = ret.get("stdout", "").strip()
        if not size:
            raise OpenShiftCheckException(
                "This host's Docker reports it is using a storage pool named '{pool}'.\n"
                "which we expect to come from local VG '{vg}'.\n"
                "However, /sbin/vgs did not find this VG. Is Docker for this host"
                "running and using the storage on the host?".format(pool=pool, vg=vg_name)
            )
        return size

    @staticmethod
    def _convert_to_bytes(string):
        units = dict(
            b=1,
            k=1024,
            m=1024**2,
            g=1024**3,
            t=1024**4,
            p=1024**5,
        )
        string = string or ""
        match = re.match(r'(\d+(?:\.\d+)?)\s*(\w)?', string)  # float followed by optional unit
        if not match:
            raise ValueError("Cannot convert to a byte size: " + string)

        number, unit = match.groups()
        multiplier = 1 if not unit else units.get(unit.lower())
        if not multiplier:
            raise ValueError("Cannot convert to a byte size: " + string)

        return float(number) * multiplier
