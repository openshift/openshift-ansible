#!/usr/bin/env python
# vim: expandtab:tabstop=4:shiftwidth=4

import argparse
import os
import ansibleutil
import sys

class Program(object):
    def __init__(self):
        self.file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)))
        self.parse_cli_args()
        self.ansible = ansibleutil.AnsibleUtil()

        inv = self.ansible.get_inventory()
        #print inv.keys()
        #sys.exit()

        if self.args.list_environments:
            self.list_environments()
            sys.exit()

        if self.args.list_groups:
            self.list_security_groups()
            sys.exit()

    def parse_cli_args(self):
        parser = argparse.ArgumentParser(
            description='OpenShift Online Operations Parallel SSH'
        )

        parser.add_argument("-v", '--verbosity', action="count",
                            help="increase output verbosity")

        group = parser.add_mutually_exclusive_group()

        group.add_argument('--list-environments', action="store_true",
                            help='List all environments')
        group.add_argument('--list-groups', action="store_true",
                            help='List all security groups')
        group.add_argument('-e', '--environment',
                            help='Set the environment')

        self.args = parser.parse_args()

    def list_environments(self):
        envs = self.ansible.get_environments()
        print
        print "Environments"
        print "------------"
        for env in envs:
            print env
        print

    def list_security_groups(self):
        envs = self.ansible.get_security_groups()
        print
        print "Groups"
        print "------"
        for env in envs:
            print env
        print


if __name__ == '__main__':
    p = Program()
