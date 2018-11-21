"""Ansible action plugin to decode ignition payloads"""

import base64
import os
import six
from six.moves import urllib
from ansible.plugins.action import ActionBase


# pylint: disable=too-many-function-args
def get_file_data(encoded_contents):
    """Decode data URLs as specified in RFC 2397"""
    # The following source is adapted from Python3 source
    # License: https://github.com/python/cpython/blob/3.7/LICENSE
    # retrieved from: https://github.com/python/cpython/blob/3.7/Lib/urllib/request.py
    _, data = encoded_contents.split(":", 1)
    mediatype, data = data.split(",", 1)

    # even base64 encoded data URLs might be quoted so unquote in any case:
    data = urllib.parse.unquote(data)
    if mediatype.endswith(";base64"):
        data = base64.b64decode(data).decode('utf-8')
        mediatype = mediatype[:-7]
    # End PSF software
    return data


# pylint: disable=too-many-function-args
def get_files(files_dict, systemd_dict, dir_list, data):
    """parse data to populate file_dict"""
    files = data.get('storage', []).get('files', [])
    for item in files:
        path = item["path"]
        dir_list.add(os.path.dirname(path))
        # remove prefix "data:,"
        encoded_contents = item['contents']['source']
        contents = get_file_data(encoded_contents)
        # convert from int to octal, padding at least to 4 places.
        # eg, 420 becomes '0644'
        mode = str(format(int(item["mode"]), '04o'))
        inode = {"contents": contents, "mode": mode}
        files_dict[path] = inode
    # get the systemd units files we're here
    systemd_units = data.get('systemd', []).get('units', [])
    for item in systemd_units:
        contents = item['contents']
        if six.PY2:
            # pylint: disable=redefined-variable-type
            contents = contents.decode('unicode-escape')
        mode = "0644"
        inode = {"contents": contents, "mode": mode}
        name = item['name']
        path = '/etc/systemd/system/' + name
        dir_list.add(os.path.dirname(path))
        files_dict[path] = inode
        enabled = item.get('enabled') or True
        systemd_dict[name] = enabled


# pylint: disable=too-few-public-methods
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
