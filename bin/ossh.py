#!/usr/bin/env python

import argparse
import ansibleutil
import sys
import os


# use dynamic inventory
# list instances
# symlinked to ~/bin
# list instances that match pattern
# python!


class Ossh(object):
    def __init__(self):
        self.file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)))
        self.parse_cli_args()
        self.ansible = ansibleutil.AnsibleUtil()

        self.list_hosts()
        
    def parse_cli_args(self):
        parser = argparse.ArgumentParser(description='Openshift Online SSH Tool.')
        parser.add_argument('-l', '--list', default=True, 
                          action="store_true", help="list out hosts")

        self.args = parser.parse_args()

    def list_hosts(self):
        # TODO: perform a numerical sort on these hosts
        # and display them
        print self.ansible.get_host_address()

    def ssh(self):
        pass

def main():
    ossh = Ossh()


if __name__ == '__main__':
    main()

