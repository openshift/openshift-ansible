#!/usr/bin/env python2
'''
    Fetch and combine multiple ec2 account settings into a single
    json hash.
'''
# vim: expandtab:tabstop=4:shiftwidth=4

from time import time
import argparse
import yaml
import os
import subprocess
import json
import errno
import fcntl
import tempfile
import copy

CONFIG_FILE_NAME = 'multi_ec2.yaml'
DEFAULT_CACHE_PATH = os.path.expanduser('~/.ansible/tmp/multi_ec2_inventory.cache')

class MultiEc2(object):
    '''
       MultiEc2 class:
            Opens a yaml config file and reads aws credentials.
            Stores a json hash of resources in result.
    '''

    def __init__(self, args=None):
        # Allow args to be passed when called as a library
        if not args:
            self.args = {}
        else:
            self.args = args

        self.cache_path = DEFAULT_CACHE_PATH
        self.config = None
        self.all_ec2_results = {}
        self.result = {}
        self.file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)))

        same_dir_config_file = os.path.join(self.file_path, CONFIG_FILE_NAME)
        etc_dir_config_file = os.path.join(os.path.sep, 'etc', 'ansible', CONFIG_FILE_NAME)

        # Prefer a file in the same directory, fall back to a file in etc
        if os.path.isfile(same_dir_config_file):
            self.config_file = same_dir_config_file
        elif os.path.isfile(etc_dir_config_file):
            self.config_file = etc_dir_config_file
        else:
            self.config_file = None # expect env vars


    def run(self):
        '''This method checks to see if the local
           cache is valid for the inventory.

           if the cache is valid; return cache
           else the credentials are loaded from multi_ec2.yaml or from the env
           and we attempt to get the inventory from the provider specified.
        '''
        # load yaml
        if self.config_file and os.path.isfile(self.config_file):
            self.config = self.load_yaml_config()
        elif os.environ.has_key("AWS_ACCESS_KEY_ID") and \
             os.environ.has_key("AWS_SECRET_ACCESS_KEY"):
            # Build a default config
            self.config = {}
            self.config['accounts'] = [
                {
                    'name': 'default',
                    'cache_location': DEFAULT_CACHE_PATH,
                    'provider': 'aws/hosts/ec2.py',
                    'env_vars': {
                        'AWS_ACCESS_KEY_ID':     os.environ["AWS_ACCESS_KEY_ID"],
                        'AWS_SECRET_ACCESS_KEY': os.environ["AWS_SECRET_ACCESS_KEY"],
                    }
                },
            ]

            self.config['cache_max_age'] = 300
        else:
            raise RuntimeError("Could not find valid ec2 credentials in the environment.")

        if self.config.has_key('cache_location'):
            self.cache_path = self.config['cache_location']

        if self.args.get('refresh_cache', None):
            self.get_inventory()
            self.write_to_cache()
        # if its a host query, fetch and do not cache
        elif self.args.get('host', None):
            self.get_inventory()
        elif not self.is_cache_valid():
            # go fetch the inventories and cache them if cache is expired
            self.get_inventory()
            self.write_to_cache()
        else:
            # get data from disk
            self.get_inventory_from_cache()

    def load_yaml_config(self, conf_file=None):
        """Load a yaml config file with credentials to query the
        respective cloud for inventory.
        """
        config = None

        if not conf_file:
            conf_file = self.config_file

        with open(conf_file) as conf:
            config = yaml.safe_load(conf)

        return config

    def get_provider_tags(self, provider, env=None):
        """Call <provider> and query all of the tags that are usuable
        by ansible.  If environment is empty use the default env.
        """
        if not env:
            env = os.environ

        # Allow relatively path'd providers in config file
        if os.path.isfile(os.path.join(self.file_path, provider)):
            provider = os.path.join(self.file_path, provider)

        # check to see if provider exists
        if not os.path.isfile(provider) or not os.access(provider, os.X_OK):
            raise RuntimeError("Problem with the provider.  Please check path " \
                        "and that it is executable. (%s)" % provider)

        cmds = [provider]
        if self.args.get('host', None):
            cmds.append("--host")
            cmds.append(self.args.get('host', None))
        else:
            cmds.append('--list')

        cmds.append('--refresh-cache')

        return subprocess.Popen(cmds, stderr=subprocess.PIPE, \
                                stdout=subprocess.PIPE, env=env)

    @staticmethod
    def generate_config(config_data):
        """Generate the ec2.ini file in as a secure temp file.
           Once generated, pass it to the ec2.py as an environment variable.
        """
        fildes, tmp_file_path = tempfile.mkstemp(prefix='multi_ec2.ini.')
        for section, values in config_data.items():
            os.write(fildes, "[%s]\n" % section)
            for option, value  in values.items():
                os.write(fildes, "%s = %s\n" % (option, value))
        os.close(fildes)
        return tmp_file_path

    def run_provider(self):
        '''Setup the provider call with proper variables
           and call self.get_provider_tags.
        '''
        try:
            all_results = []
            tmp_file_paths = []
            processes = {}
            for account in self.config['accounts']:
                env = account['env_vars']
                if account.has_key('provider_config'):
                    tmp_file_paths.append(MultiEc2.generate_config(account['provider_config']))
                    env['EC2_INI_PATH'] = tmp_file_paths[-1]
                name = account['name']
                provider = account['provider']
                processes[name] = self.get_provider_tags(provider, env)

            # for each process collect stdout when its available
            for name, process in processes.items():
                out, err = process.communicate()
                all_results.append({
                    "name": name,
                    "out": out.strip(),
                    "err": err.strip(),
                    "code": process.returncode
                })

        finally:
            # Clean up the mkstemp file
            for tmp_file in tmp_file_paths:
                os.unlink(tmp_file)

        return all_results

    def get_inventory(self):
        """Create the subprocess to fetch tags from a provider.
        Host query:
        Query to return a specific host.  If > 1 queries have
        results then fail.

        List query:
        Query all of the different accounts for their tags.  Once completed
        store all of their results into one merged updated hash.
        """
        provider_results = self.run_provider()

        # process --host results
        # For any 0 result, return it
        if self.args.get('host', None):
            count = 0
            for results in provider_results:
                if results['code'] == 0 and results['err'] == '' and results['out'] != '{}':
                    self.result = json.loads(results['out'])
                    count += 1
                if count > 1:
                    raise RuntimeError("Found > 1 results for --host %s. \
                                       This is an invalid state." % self.args.get('host', None))
        # process --list results
        else:
            # For any non-zero, raise an error on it
            for result in provider_results:
                if result['code'] != 0:
                    err_msg = ['\nProblem fetching account: {name}',
                               'Error Code: {code}',
                               'StdErr: {err}',
                               'Stdout: {out}',
                              ]
                    raise RuntimeError('\n'.join(err_msg).format(**result))
                else:
                    self.all_ec2_results[result['name']] = json.loads(result['out'])

            # Check if user wants extra vars in yaml by
            # having hostvars and all_group defined
            for acc_config in self.config['accounts']:
                self.apply_account_config(acc_config)

            # Build results by merging all dictionaries
            values = self.all_ec2_results.values()
            values.insert(0, self.result)
            for result in  values:
                MultiEc2.merge_destructively(self.result, result)

    def apply_account_config(self, acc_config):
        ''' Apply account config settings
        '''
        if not acc_config.has_key('hostvars') and not acc_config.has_key('all_group'):
            return

        results = self.all_ec2_results[acc_config['name']]
       # Update each hostvar with the newly desired key: value
        for host_property, value in acc_config['hostvars'].items():
            # Verify the account results look sane
            # by checking for these keys ('_meta' and 'hostvars' exist)
            if results.has_key('_meta') and results['_meta'].has_key('hostvars'):
                for data in results['_meta']['hostvars'].values():
                    data[str(host_property)] = str(value)

            # Add this group
            if results.has_key(acc_config['all_group']):
                results["%s_%s" % (host_property, value)] = \
                  copy.copy(results[acc_config['all_group']])

        # store the results back into all_ec2_results
        self.all_ec2_results[acc_config['name']] = results

    @staticmethod
    def merge_destructively(input_a, input_b):
        "merges b into input_a"
        for key in input_b:
            if key in input_a:
                if isinstance(input_a[key], dict) and isinstance(input_b[key], dict):
                    MultiEc2.merge_destructively(input_a[key], input_b[key])
                elif input_a[key] == input_b[key]:
                    pass # same leaf value
                # both lists so add each element in b to a if it does ! exist
                elif isinstance(input_a[key], list) and isinstance(input_b[key], list):
                    for result in input_b[key]:
                        if result not in input_a[key]:
                            input_a[key].append(result)
                # a is a list and not b
                elif isinstance(input_a[key], list):
                    if input_b[key] not in input_a[key]:
                        input_a[key].append(input_b[key])
                elif isinstance(input_b[key], list):
                    input_a[key] = [input_a[key]] + [k for k in input_b[key] if k != input_a[key]]
                else:
                    input_a[key] = [input_a[key], input_b[key]]
            else:
                input_a[key] = input_b[key]
        return input_a

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

        parser = argparse.ArgumentParser(
            description='Produce an Ansible Inventory file based on a provider')
        parser.add_argument('--refresh-cache', action='store_true', default=False,
                            help='Fetch cached only instances (default: False)')
        parser.add_argument('--list', action='store_true', default=True,
                            help='List instances (default: True)')
        parser.add_argument('--host', action='store', default=False,
                            help='Get all the variables about a specific instance')
        self.args = parser.parse_args().__dict__

    def write_to_cache(self):
        ''' Writes data in JSON format to a file '''

        # if it does not exist, try and create it.
        if not os.path.isfile(self.cache_path):
            path = os.path.dirname(self.cache_path)
            try:
                os.makedirs(path)
            except OSError as exc:
                if exc.errno != errno.EEXIST or not os.path.isdir(path):
                    raise

        json_data = MultiEc2.json_format_dict(self.result, True)
        with open(self.cache_path, 'w') as cache:
            try:
                fcntl.flock(cache, fcntl.LOCK_EX)
                cache.write(json_data)
            finally:
                fcntl.flock(cache, fcntl.LOCK_UN)

    def get_inventory_from_cache(self):
        ''' Reads the inventory from the cache file and returns it as a JSON
        object '''

        if not os.path.isfile(self.cache_path):
            return None

        with open(self.cache_path, 'r') as cache:
            self.result = json.loads(cache.read())

        return True

    @classmethod
    def json_format_dict(cls, data, pretty=False):
        ''' Converts a dict to a JSON object and dumps it as a formatted
        string '''

        if pretty:
            return json.dumps(data, sort_keys=True, indent=2)
        else:
            return json.dumps(data)

    def result_str(self):
        '''Return cache string stored in self.result'''
        return self.json_format_dict(self.result, True)


if __name__ == "__main__":
    MEC2 = MultiEc2()
    MEC2.parse_cli_args()
    MEC2.run()
    print MEC2.result_str()
