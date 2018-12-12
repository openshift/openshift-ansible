'''
 Unit tests for wildcard
'''
import json
import os
import sys

MODULE_PATH = os.path.realpath(os.path.join(__file__, os.pardir, os.pardir, 'action_plugins'))
sys.path.insert(0, MODULE_PATH)
ASSET_PATH = os.path.realpath(os.path.join(__file__, os.pardir, 'test_data'))

# pylint: disable=import-error,wrong-import-position,missing-docstring
import parse_ignition  # noqa: E402


def read_ign(path):
    with open(path) as ign_in:
        data = json.loads(ign_in.read())
    return data


def write_out_files(files_dict):
    for path in files_dict:
        with open('/tmp/bsoutput/' + path.replace('/', '__'), 'w') as fpath:
            fpath.write(files_dict[path]['contents'])


def test_parse_json():
    ign_data = read_ign(os.path.join(ASSET_PATH, 'example.ign.json'))
    files_dict = {}
    systemd_dict = {}
    dir_list = set()
    result = {}
    result['files_dict'] = files_dict
    result['systemd_dict'] = systemd_dict
    parse_ignition.get_files(files_dict, systemd_dict, dir_list, ign_data)


def test_parse_json_encoded_files():
    ign_data = read_ign(os.path.join(ASSET_PATH, 'bootstrap.ign.json'))
    files_dict = {}
    systemd_dict = {}
    dir_list = set()
    result = {}
    result['files_dict'] = files_dict
    result['systemd_dict'] = systemd_dict
    parse_ignition.get_files(files_dict, systemd_dict, dir_list, ign_data)
    # print(files_dict['/opt/tectonic/manifests/cluster-config.yaml']['contents'])


def parse_json2():
    ign_data = read_ign(os.path.join(ASSET_PATH, 'bs.ign.json'))
    files_dict = {}
    systemd_dict = {}
    dir_list = set()
    result = {}
    result['files_dict'] = files_dict
    result['systemd_dict'] = systemd_dict
    parse_ignition.get_files(files_dict, systemd_dict, dir_list, ign_data)
    write_out_files(files_dict)


if __name__ == '__main__':
    test_parse_json()
    test_parse_json_encoded_files()
    parse_json2()
