#!/usr/bin/env python

from time import time
import argparse
import yaml
import os
import sys
import pdb
import subprocess
import json
import pprint


class MultiEc2(object):

    def __init__(self):
        self.config = None
        self.all_ec2_results = {}
        self.result = {}
        self.cache_path = os.path.expanduser('~/.ansible/tmp/multi_ec2_inventory.cache')
        self.file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)))
        self.config_file = os.path.join(self.file_path,"multi_ec2.yaml")
        self.parse_cli_args()

        # load yaml
        if os.path.isfile(self.config_file):
            self.config = self.load_yaml_config()
        elif os.environ.has_key("AWS_ACCESS_KEY_ID") and os.environ.has_key("AWS_SECRET_ACCESS_KEY"):
            self.config = {}
            self.config['accounts'] = [
                {
                    'name': 'default',
                    'provider': 'aws/ec2.py',
                    'env_vars': {
                        'AWS_ACCESS_KEY_ID':     os.environ["AWS_ACCESS_KEY_ID"],
                        'AWS_SECRET_ACCESS_KEY': os.environ["AWS_SECRET_ACCESS_KEY"],
                    }
                },
            ]

            self.config['cache_max_age'] = 0
        else:
            raise RuntimeError("Could not find valid ec2 credentials in the environment.")


        # if its a host query, fetch and do not cache
        if self.args.host:
            self.get_inventory()
        elif not self.is_cache_valid():
            # go fetch the inventories and cache them if cache is expired
            self.get_inventory()
            self.write_to_cache()
        else:
            # get data from disk
            self.get_inventory_from_cache()

    def load_yaml_config(self,conf_file=None):
        """Load a yaml config file with credentials to query the
        respective cloud for inventory.
        """
        config = None

        if not conf_file:
            conf_file = self.config_file

        with open(conf_file) as conf:
            config = yaml.safe_load(conf)

        return config

    def get_provider_tags(self,provider, env={}):
        """Call <provider> and query all of the tags that are usuable
        by ansible.  If environment is empty use the default env.
        """
        if not env:
            env = os.environ

        # check to see if provider exists
        if not os.path.isfile(provider) or not os.access(provider, os.X_OK):
            raise RuntimeError("Problem with the provider.  Please check path " \
                        "and that it is executable. (%s)" % provider)

        cmds = [provider]
        if self.args.host:
            cmds.append("--host")
            cmds.append(self.args.host)
        else:
            cmds.append('--list')

        cmds.append('--refresh-cache')

        return subprocess.Popen(cmds, stderr=subprocess.PIPE, \
                                stdout=subprocess.PIPE, env=env)
    def get_inventory(self):
        """Create the subprocess to fetch tags from a provider.
        Host query:
        Query to return a specific host.  If > 1 queries have
        results then fail.

        List query:
        Query all of the different accounts for their tags.  Once completed
        store all of their results into one merged updated hash.
        """
        processes = {}
        for account in self.config['accounts']:
            env = account['env_vars']
            name = account['name']
            provider = account['provider']
            processes[name] = self.get_provider_tags(provider, env)

        # for each process collect stdout when its available
        all_results = []
        for name, process in processes.items():
            out, err = process.communicate()
            all_results.append({
                "name": name,
                "out": out.strip(),
                "err": err.strip(),
                "code": process.returncode
            })

        if not self.args.host:
            # For any non-zero, raise an error on it
            for result in all_results:
                if result['code'] != 0:
                    raise RuntimeError(result['err'])
                else:
                    self.all_ec2_results[result['name']] = json.loads(result['out'])
            values = self.all_ec2_results.values()
            values.insert(0, self.result)
            [self.merge_destructively(self.result, x) for x in  values]
        else:
            # For any 0 result, return it
            count = 0
            for results in all_results:
                if results['code'] == 0 and results['err'] == '' and results['out'] != '{}':
                    self.result = json.loads(out)
                    count += 1
                if count > 1:
                    raise RuntimeError("Found > 1 results for --host %s. \
                                       This is an invalid state." % self.args.host)
    def merge_destructively(self, a, b):
        "merges b into a"
        for key in b:
            if key in a:
                if isinstance(a[key], dict) and isinstance(b[key], dict):
                    self.merge_destructively(a[key], b[key])
                elif a[key] == b[key]:
                    pass # same leaf value
                # both lists so add each element in b to a if it does ! exist
                elif isinstance(a[key], list) and isinstance(b[key],list):
                    for x in b[key]:
                        if x not in a[key]:
                            a[key].append(x)
                # a is a list and not b
                elif isinstance(a[key], list):
                    if b[key] not in a[key]:
                        a[key].append(b[key])
                elif isinstance(b[key], list):
                    a[key] = [a[key]] + [k for k in b[key] if k != a[key]]
                else:
                    a[key] = [a[key],b[key]]
            else:
                a[key] = b[key]
        return a

    def is_cache_valid(self):
        ''' Determines if the cache files have expired, or if it is still valid '''

        if os.path.isfile(self.cache_path):
            mod_time = os.path.getmtime(self.cache_path)
            current_time = time()
            if (mod_time + self.config['cache_max_age']) > current_time:
                return True

        return False

    def parse_cli_args(self):
        ''' Command line argument processing '''

        parser = argparse.ArgumentParser(description='Produce an Ansible Inventory file based on a provider')
        parser.add_argument('--list', action='store_true', default=True,
                           help='List instances (default: True)')
        parser.add_argument('--host', action='store',
                           help='Get all the variables about a specific instance')
        self.args = parser.parse_args()

    def write_to_cache(self):
        ''' Writes data in JSON format to a file '''

        json_data = self.json_format_dict(self.result, True)
        with open(self.cache_path, 'w') as cache:
            cache.write(json_data)

    def get_inventory_from_cache(self):
        ''' Reads the inventory from the cache file and returns it as a JSON
        object '''

        with open(self.cache_path, 'r') as cache:
            self.result = json.loads(cache.read())

    def json_format_dict(self, data, pretty=False):
        ''' Converts a dict to a JSON object and dumps it as a formatted
        string '''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

    def result_str(self):
        return self.json_format_dict(self.result, True)


if __name__ == "__main__":
    mi = MultiEc2()
    print mi.result_str()
