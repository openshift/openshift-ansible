# (c) 2017, Red Hat Inc.
#
# This is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Ansible is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

"""
This is a copy of the "package" action plugin from Ansible,
with minor modifications to implement retries.
"""

# pylint: skip-file

from __future__ import (absolute_import, division, print_function)
__metaclass__ = type

import time

from ansible.plugins.action import ActionBase

try:
    from __main__ import display
except ImportError:
    from ansible.utils.display import Display
    display = Display()


class ActionModule(ActionBase):

    TRANSFERS_FILES = False

    def run(self, tmp=None, task_vars=None):
        ''' handler for package operations '''

        self._supports_check_mode = True
        self._supports_async = True

        result = super(ActionModule, self).run(tmp, task_vars)

        module = self._task.args.get('use', 'auto')

        if module == 'auto':
            try:
                if self._task.delegate_to:  # if we delegate, we should use delegated host's facts
                    module = self._templar.template("{{hostvars['%s']['ansible_pkg_mgr']}}" % self._task.delegate_to)
                else:
                    module = self._templar.template('{{ansible_pkg_mgr}}')
            except Exception:
                pass  # could not get it from template!

        if module == 'auto':
            module_args = dict(filter='ansible_pkg_mgr', gather_subset='!all')
            facts = self._execute_module(module_name='setup', module_args=module_args, task_vars=task_vars)
            display.debug("Facts %s" % facts)
            if 'ansible_facts' in facts and 'ansible_pkg_mgr' in facts['ansible_facts']:
                module = getattr(facts['ansible_facts'], 'ansible_pkg_mgr', 'auto')

        if module != 'auto':

            if module not in self._shared_loader_obj.module_loader:
                result['failed'] = True
                result['msg'] = 'Could not find a module for %s.' % module
            else:
                # run the 'package' module
                new_module_args = self._task.args.copy()
                if 'use' in new_module_args:
                    del new_module_args['use']

                display.vvvv("Running {}".format(module))
                tries = 0
                while True:
                    res = self._execute_module(
                        module_name=module,
                        module_args=new_module_args,
                        task_vars=task_vars,
                        wrap_async=self._task.async,
                    )
                    tries += 1
                    if tries > 3 or not res.get('failed'):
                        result.update(res)
                        break
                    result['last_failed'] = res
                    display.v("{} module failed on try {} with result: {}".format(module, tries, res))
                    time.sleep(5)
        else:
            result['failed'] = True
            result['msg'] = 'Could not detect which package manager to use. Try gathering facts or setting the "use" option.'

        return result
