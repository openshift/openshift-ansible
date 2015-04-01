#!/usr/bin/python
# -*- coding: utf-8 -*-
# vim: expandtab:tabstop=4:shiftwidth=4

from subprocess import call, check_output

DOCUMENTATION = '''
---
module: os_firewall_manage_iptables
short_description: This module manages iptables rules for a given chain
author: Jason DeTiberus
requirements: [ ]
'''
EXAMPLES = '''
'''


class IpTablesError(Exception):
    def __init__(self, msg, cmd, exit_code, output):
        self.msg = msg
        self.cmd = cmd
        self.exit_code = exit_code
        self.output = output


class IpTablesAddRuleError(IpTablesError):
    pass


class IpTablesRemoveRuleError(IpTablesError):
    pass


class IpTablesSaveError(IpTablesError):
    pass


class IpTablesCreateChainError(IpTablesError):
    def __init__(self, chain, msg, cmd, exit_code, output):
        super(IpTablesCreateChainError, self).__init__(msg, cmd, exit_code, output)
        self.chain = chain


class IpTablesCreateJumpRuleError(IpTablesError):
    def __init__(self, chain, msg, cmd, exit_code, output):
        super(IpTablesCreateJumpRuleError, self).__init__(msg, cmd, exit_code,
                                                          output)
        self.chain = chain


# TODO: impliment rollbacks for any events that where successful and an
# exception was thrown later. for example, when the chain is created
# successfully, but the add/remove rule fails.
class IpTablesManager:
    def __init__(self, module):
        self.module = module
        self.ip_version = module.params['ip_version']
        self.check_mode = module.check_mode
        self.chain = module.params['chain']
        self.create_jump_rule = module.params['create_jump_rule']
        self.jump_rule_chain = module.params['jump_rule_chain']
        self.cmd = self.gen_cmd()
        self.save_cmd = self.gen_save_cmd()
        self.output = []
        self.changed = False

    def save(self):
        try:
            self.output.append(check_output(self.save_cmd,
                                            stderr=subprocess.STDOUT))
        except subprocess.CalledProcessError as e:
            raise IpTablesSaveError(
                msg="Failed to save iptables rules",
                cmd=e.cmd, exit_code=e.returncode, output=e.output)

    def verify_chain(self):
        if not self.chain_exists():
            self.create_chain()
        if self.create_jump_rule and not self.jump_rule_exists():
            self.create_jump()

    def add_rule(self, port, proto):
        rule = self.gen_rule(port, proto)
        if not self.rule_exists(rule):
            self.verify_chain()

            if self.check_mode:
                self.changed = True
                self.output.append("Create rule for %s %s" % (proto, port))
            else:
                cmd = self.cmd + ['-A'] + rule
                try:
                    self.output.append(check_output(cmd))
                    self.changed = True
                    self.save()
                except subprocess.CalledProcessError as e:
                    raise IpTablesCreateChainError(
                        chain=self.chain,
                        msg="Failed to create rule for "
                            "%s %s" % (self.proto, self.port),
                        cmd=e.cmd, exit_code=e.returncode,
                        output=e.output)

    def remove_rule(self, port, proto):
        rule = self.gen_rule(port, proto)
        if self.rule_exists(rule):
            if self.check_mode:
                self.changed = True
                self.output.append("Remove rule for %s %s" % (proto, port))
            else:
                cmd = self.cmd + ['-D'] + rule
                try:
                    self.output.append(check_output(cmd))
                    self.changed = True
                    self.save()
                except subprocess.CalledProcessError as e:
                    raise IpTablesRemoveChainError(
                        chain=self.chain,
                        msg="Failed to remove rule for %s %s" % (proto, port),
                        cmd=e.cmd, exit_code=e.returncode, output=e.output)

    def rule_exists(self, rule):
        check_cmd = self.cmd + ['-C'] + rule
        return True if subprocess.call(check_cmd) == 0 else False

    def gen_rule(self, port, proto):
        return [self.chain, '-p', proto, '-m', 'state', '--state', 'NEW',
                '-m', proto, '--dport', str(port), '-j', 'ACCEPT']

    def create_jump(self):
        if self.check_mode:
            self.changed = True
            self.output.append("Create jump rule for chain %s" % self.chain)
        else:
            try:
                cmd = self.cmd + ['-L', self.jump_rule_chain, '--line-numbers']
                output = check_output(cmd, stderr=subprocess.STDOUT)

                # break the input rules into rows and columns
                input_rules = map(lambda s: s.split(), output.split('\n'))

                # Find the last numbered rule
                last_rule_num = None
                last_rule_target = None
                for rule in input_rules[:-1]:
                    if rule:
                        try:
                            last_rule_num = int(rule[0])
                        except ValueError:
                            continue
                        last_rule_target = rule[1]

                # Raise an exception if we do not find a valid rule
                if not last_rule_num or not last_rule_target:
                   raise IpTablesCreateJumpRuleError(
                        chain=self.chain,
                        msg="Failed to find existing %s rules" % self.jump_rule_chain,
                        cmd=None, exit_code=None, output=None)

                # Naively assume that if the last row is a REJECT rule, then
                # we can add insert our rule right before it, otherwise we
                # assume that we can just append the rule.
                if last_rule_target == 'REJECT':
                    # insert rule
                    cmd = self.cmd + ['-I', self.jump_rule_chain, str(last_rule_num)]
                else:
                    # append rule
                    cmd = self.cmd + ['-A', self.jump_rule_chain]
                cmd += ['-j', self.chain]
                output = check_output(cmd, stderr=subprocess.STDOUT)
                changed = True
                self.output.append(output)
                self.save()
            except subprocess.CalledProcessError as e:
                if '--line-numbers' in e.cmd:
                    raise IpTablesCreateJumpRuleError(
                        chain=self.chain,
                        msg="Failed to query existing %s rules to " % self.jump_rule_chain +
                            "determine jump rule location",
                        cmd=e.cmd, exit_code=e.returncode,
                        output=e.output)
                else:
                    raise IpTablesCreateJumpRuleError(
                        chain=self.chain,
                        msg="Failed to create jump rule for chain %s" %
                            self.chain,
                        cmd=e.cmd, exit_code=e.returncode,
                        output=e.output)

    def create_chain(self):
        if self.check_mode:
            self.changed = True
            self.output.append("Create chain %s" % self.chain)
        else:
            try:
                cmd = self.cmd + ['-N', self.chain]
                self.output.append(check_output(cmd,
                                                stderr=subprocess.STDOUT))
                self.changed = True
                self.output.append("Successfully created chain %s" %
                                   self.chain)
                self.save()
            except subprocess.CalledProcessError as e:
                raise IpTablesCreateChainError(
                    chain=self.chain,
                    msg="Failed to create chain: %s" % self.chain,
                    cmd=e.cmd, exit_code=e.returncode, output=e.output
                    )

    def jump_rule_exists(self):
        cmd = self.cmd + ['-C', self.jump_rule_chain, '-j', self.chain]
        return True if subprocess.call(cmd) == 0 else False

    def chain_exists(self):
        cmd = self.cmd + ['-L', self.chain]
        return True if subprocess.call(cmd) == 0 else False

    def gen_cmd(self):
        cmd = 'iptables' if self.ip_version == 'ipv4' else 'ip6tables'
        return ["/usr/sbin/%s" % cmd]

    def gen_save_cmd(self):
        cmd = 'iptables' if self.ip_version == 'ipv4' else 'ip6tables'
        return ['/usr/libexec/iptables/iptables.init', 'save']


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(required=True),
            action=dict(required=True, choices=['add', 'remove', 'verify_chain']),
            chain=dict(required=False, default='OS_FIREWALL_ALLOW'),
            create_jump_rule=dict(required=False, type='bool', default=True),
            jump_rule_chain=dict(required=False, default='INPUT'),
            protocol=dict(required=False, choices=['tcp', 'udp']),
            port=dict(required=False, type='int'),
            ip_version=dict(required=False, default='ipv4',
                            choices=['ipv4', 'ipv6']),
        ),
        supports_check_mode=True
    )

    action = module.params['action']
    protocol = module.params['protocol']
    port = module.params['port']

    if action in ['add', 'remove']:
        if not protocol:
            error = "protocol is required when action is %s" % action
            module.fail_json(msg=error)
        if not port:
            error = "port is required when action is %s" % action
            module.fail_json(msg=error)

    iptables_manager = IpTablesManager(module)

    try:
        if action == 'add':
            iptables_manager.add_rule(port, protocol)
        elif action == 'remove':
            iptables_manager.remove_rule(port, protocol)
        elif action == 'verify_chain':
            iptables_manager.verify_chain()
    except IpTablesError as e:
        module.fail_json(msg=e.msg)

    return module.exit_json(changed=iptables_manager.changed,
                            output=iptables_manager.output)


# import module snippets
from ansible.module_utils.basic import *
if __name__ == '__main__':
    main()
