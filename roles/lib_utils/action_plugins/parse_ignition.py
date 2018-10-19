"""Ansible action plugin to decode ignition payloads"""

import base64
import os

from ansible.plugins.action import ActionBase
from ansible import errors
from six.moves import urllib


def get_files(files_dict, systemd_dict, dir_list, data):
    """parse data to populate file_dict"""
    files = data.get('storage', []).get('files', [])
    for item in files:
        path = item["path"]
        dir_list.add(os.path.dirname(path))
        # remove prefix "data:,"
        encoding, contents = item['contents']['source'].split(',', 1)
        if 'base64' in encoding:
            contents = base64.b64decode(contents).decode('utf-8')
        else:
            contents = urllib.parse.unquote(contents)
        # convert from int to octal, padding at least to 4 places.
        # eg, 420 becomes '0644'
        mode = str(format(int(item["mode"]), '04o'))
        inode = {"contents": contents, "mode": mode}
        files_dict[path] = inode
    # get the systemd units files we're here
    systemd_units = data.get('systemd', []).get('units', [])
    for item in systemd_units:
        contents = item['contents']
        mode = "0644"
        inode = {"contents": contents, "mode": mode}
        name = item['name']
        path = '/etc/systemd/system/' + name
        dir_list.add(os.path.dirname(path))
        files_dict[path] = inode
        enabled = item.get('enabled') or True
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
