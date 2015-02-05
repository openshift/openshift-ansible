# vim: expandtab:tabstop=4:shiftwidth=4

import subprocess
import sys
import os
import json
import re

class AnsibleUtil(object):
    def __init__(self):
        self.file_path = os.path.join(os.path.dirname(os.path.realpath(__file__)))
        self.multi_ec2_path = os.path.realpath(os.path.join(self.file_path, '..','inventory','multi_ec2.py'))

    def get_inventory(self,args=[]):
        cmd = [self.multi_ec2_path]

        if args:
            cmd.extend(args)

        env = {}
        p = subprocess.Popen(cmd, stderr=subprocess.PIPE,
                         stdout=subprocess.PIPE, env=env)

        out,err = p.communicate()

        if p.returncode != 0:
            raise RuntimeError(err)

        return json.loads(out.strip())

    def get_environments(self):
        pattern = re.compile(r'^tag_environment_(.*)')

        envs = []
        inv = self.get_inventory()
        for key in inv.keys():
            m = pattern.match(key)
            if m:
                envs.append(m.group(1))

        return envs

    def get_security_groups(self):
        pattern = re.compile(r'^security_group_(.*)')

        groups = []
        inv = self.get_inventory()
        for key in inv.keys():
            m = pattern.match(key)
            if m:
                groups.append(m.group(1))

        return groups

    def build_host_dict(self, args=[]):
        inv = self.get_inventory(args)

        inst_by_env = {}
        for dns, host in inv['_meta']['hostvars'].items():
            if host['ec2_tag_environment'] not in inst_by_env:
                inst_by_env[host['ec2_tag_environment']] = {}
            host_id = "%s:%s" % (host['ec2_tag_Name'],host['ec2_id'])
            inst_by_env[host['ec2_tag_environment']][host_id] = host


        return inst_by_env



