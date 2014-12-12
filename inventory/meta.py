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


class MetaInventory(object):

    def __init__(self):
        self.config = None
        self.results = {}
        self.result = {}
        self.cache_path_cache = os.path.expanduser('~/.ansible/tmp/meta-inventory.cache')

        self.parse_cli_args()

        # load yaml
        self.load_yaml_config()

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

    def load_yaml_config(self,conf_file=os.path.join(os.getcwd(),'meta.yaml')):
        """Load a yaml config file with credentials to query the
        respective cloud for inventory.
        """
        config = None
        with open(conf_file) as conf:
          self.config = yaml.safe_load(conf)

    def get_provider_tags(self,provider, env={}):
        """Call <provider> and query all of the tags that are usuable
        by ansible.  If environment is empty use the default env.
        """
        if not env:
            env = os.environ

        # check to see if provider exists
        if not os.path.isfile(os.path.join(os.getcwd(),provider)):
            raise RuntimeError("Unkown provider: %s" % provider)

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
        Query all of the different clouds for their tags.  Once completed
        store all of their results into one merged updated hash.
        """
        processes = {}
        for account in self.config['clouds']:
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
                    self.results[result['name']] = json.loads(result['out'])
            self.merge()
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

    def merge(self):
        """Merge the results into a single hash.  Duplicate keys are placed
        into a list.
        """
        for name, cloud_result in self.results.items():
            for k,v in cloud_result.items():
                if self.result.has_key(k):
                    # need to combine into a list
                    if isinstance(self.result[k], list):
                        self.result[k].append(v)
                    else:
                        self.result[k] = [self.result[k],v]
                else:
                    self.result[k] = [v]

        self.result = self.json_format_dict(self.result)

    def is_cache_valid(self):
        ''' Determines if the cache files have expired, or if it is still valid '''

        if os.path.isfile(self.cache_path_cache):
            mod_time = os.path.getmtime(self.cache_path_cache)
            current_time = time()
            if (mod_time + self.config['cache_max_age']) > current_time:
                #if os.path.isfile(self.cache_path_index):
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
        with open(self.cache_path_cache, 'w') as cache:
            cache.write(json_data)

    def get_inventory_from_cache(self):
        ''' Reads the inventory from the cache file and returns it as a JSON
        object '''

        with open(self.cache_path_cache, 'r') as cache:
            self.result = json.loads(cache.read())

    def json_format_dict(self, data, pretty=False):
        ''' Converts a dict to a JSON object and dumps it as a formatted
        string '''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)


if __name__ == "__main__":
    mi = MetaInventory()
    #print mi.result
    pp = pprint.PrettyPrinter(indent=2)
    pp.pprint(mi.result)

