# pylint: disable=missing-docstring
import json

from openshift_checks import OpenShiftCheck, OpenShiftCheckException, get_var


class DockerStorage(OpenShiftCheck):
    """Check Docker storage sanity.

    Check for thinpool usage during a containerized installation
    """

    name = "docker_storage"
    tags = ["preflight"]

    max_thinpool_data_usage_percent = 90.0
    max_thinpool_meta_usage_percent = 90.0

    @classmethod
    def is_active(cls, task_vars):
        """Only run on hosts that depend on Docker."""
        is_containerized = get_var(task_vars, "openshift", "common", "is_containerized")
        is_node = "nodes" in get_var(task_vars, "group_names", default=[])
        return (super(DockerStorage, cls).is_active(task_vars) and is_containerized) or is_node

    def run(self, tmp, task_vars):
        try:
            self.max_thinpool_data_usage_percent = float(get_var(task_vars, "max_thinpool_data_usage_percent",
                                                                 default=self.max_thinpool_data_usage_percent))
            self.max_thinpool_meta_usage_percent = float(get_var(task_vars, "max_thinpool_metadata_usage_percent",
                                                                 default=self.max_thinpool_meta_usage_percent))
        except ValueError as err:
            return {
                "failed": True,
                "msg": "Unable to convert thinpool data usage limit to float: {}".format(str(err))
            }

        err_msg = self.check_thinpool_usage(task_vars)
        if err_msg:
            return {"failed": True, "msg": err_msg}

        return {}

    def check_thinpool_usage(self, task_vars):
        lvs = self.get_lvs_data(task_vars)
        lv_data = self.extract_thinpool_obj(lvs)

        data_percent = self.get_thinpool_data_usage(lv_data)
        metadata_percent = self.get_thinpool_metadata_usage(lv_data)

        if data_percent > self.max_thinpool_data_usage_percent:
            msg = "thinpool data usage above maximum threshold of {threshold}%"
            return msg.format(threshold=self.max_thinpool_data_usage_percent)

        if metadata_percent > self.max_thinpool_meta_usage_percent:
            msg = "thinpool metadata usage above maximum threshold of {threshold}%"
            return msg.format(threshold=self.max_thinpool_meta_usage_percent)

        return ""

    def get_lvs_data(self, task_vars):
        lvs_cmd = "/sbin/lvs --select vg_name=docker --select lv_name=docker-pool --report-format json"
        result = self.exec_cmd(lvs_cmd, task_vars)

        if result.get("failed", False):
            msg = "no thinpool usage data returned by the host: {}"
            raise OpenShiftCheckException(msg.format(result.get("msg", "")))

        try:
            data_json = json.loads(result.get("stdout", ""))
        except ValueError as err:
            raise OpenShiftCheckException("Invalid JSON value returned by lvs command: {}".format(str(err)))

        data = data_json.get("report")
        if not data:
            raise OpenShiftCheckException("no thinpool usage data returned by the host.")

        return data

    @staticmethod
    def get_thinpool_data_usage(thinpool_lv_data):
        data = thinpool_lv_data.get("data_percent")
        if not data:
            raise OpenShiftCheckException("no thinpool usage data returned by the host.")

        return float(data)

    @staticmethod
    def get_thinpool_metadata_usage(thinpool_lv_data):
        data = thinpool_lv_data.get("metadata_percent")
        if not data:
            raise OpenShiftCheckException("no thinpool usage data returned by the host.")

        return float(data)

    @staticmethod
    def extract_thinpool_obj(thinpool_data):
        if not thinpool_data or not thinpool_data[0]:
            raise OpenShiftCheckException("no thinpool usage data returned by the host.")

        lv_data = thinpool_data[0].get("lv")
        if not lv_data or not lv_data[0]:
            raise OpenShiftCheckException("no thinpool usage data returned by the host.")

        return lv_data[0]

    def exec_cmd(self, cmd_str, task_vars):
        return self.execute_module("command", {
            "_raw_params": cmd_str,
        }, task_vars)
