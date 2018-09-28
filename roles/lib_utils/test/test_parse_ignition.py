'''
 Unit tests for wildcard
'''
import json
import os
import sys

MODULE_PATH = os.path.realpath(os.path.join(__file__, os.pardir, os.pardir, 'action_plugins'))
sys.path.insert(0, MODULE_PATH)

# pylint: disable=import-error,wrong-import-position,missing-docstring
import parse_ignition # noqa: E402


def read_ign(path):
    with open(path) as ign_in:
        data = json.loads(ign_in.read())
    return data


def test_parse_json():
    ign_data = read_ign('test_data/example.ign.json')
    files_dict = {}
    systemd_dict = {}
    dir_list = set()
    result = {}
    result['files_dict'] = files_dict
    result['systemd_dict'] = systemd_dict
    parse_ignition.get_files(files_dict, systemd_dict, dir_list, ign_data)


if __name__ == '__main__':
    test_parse_json()
