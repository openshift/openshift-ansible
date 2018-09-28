"""Ansible action plugin to decode ignition payloads"""

import os

from ansible.plugins.action import ActionBase
from ansible import errors
from six.moves import urllib


def get_files(files_dict, systemd_dict, dir_list, data):
    """parse data to populate file_dict"""
    for item in data['storage']['files']:
        path = item["path"]
        dir_list.add(os.path.dirname(path))
        # remove prefix "data:,"
        contents = urllib.parse.unquote(item['contents']['source'][6:])
        mode = str(item["mode"])
        inode = {"contents": contents, "mode": mode}
        files_dict[path] = inode
    # get the systemd units files we're here
    for item in data['systemd']['units']:
        contents = item['contents']
        mode = "0644"
        inode = {"contents": contents, "mode": mode}
        name = item['name']
        path = '/etc/systemd/system/' + name
        dir_list.add(os.path.dirname(path))
        files_dict[path] = inode
        enabled = item['enabled']
        systemd_dict[name] = enabled


class ActionModule(ActionBase):
    """ActionModule for parse_ignition.py"""

    def run(self, tmp=None, task_vars=None):
        """Run parse_ignition action plugin"""
        result = super(ActionModule, self).run(tmp, task_vars)
        result["changed"] = False
        result["failed"] = False
        result["msg"] = "Parsed successfully"
        files_dict = {}
        systemd_dict = {}
        dir_list = set()
        result["files_dict"] = files_dict
        result["systemd_dict"] = systemd_dict

        # self.task_vars holds all in-scope variables.
        # Ignore settting self.task_vars outside of init.
        # pylint: disable=W0201
        self.task_vars = task_vars or {}
        ign_file_contents = self._task.args.get('ign_file_contents')
        get_files(files_dict, systemd_dict, dir_list, ign_file_contents)
        result["dir_list"] = list(dir_list)
        return result
