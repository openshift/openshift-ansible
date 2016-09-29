# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""
This file is a stdout callback plugin for the OpenShift Quick
Installer. The purpose of this callback plugin is to reduce the amount
of produced output for customers and enable simpler progress checking.

What's different:

* Playbook progress is expressed as: Play <current_play>/<total_plays> (Play Name)
  Ex: Play 3/30 (Initialize Megafrobber)

* The Tasks and Handlers in each play (and included roles) are printed
  as a series of .'s following the play progress line.

"""

from __future__ import (absolute_import, print_function)
import imp
import os
import sys

ANSIBLE_PATH = imp.find_module('ansible')[1]
DEFAULT_PATH = os.path.join(ANSIBLE_PATH, 'plugins/callback/default.py')
DEFAULT_MODULE = imp.load_source(
    'ansible.plugins.callback.default',
    DEFAULT_PATH
)

try:
    from ansible.plugins.callback import CallbackBase
    BASECLASS = CallbackBase
except ImportError:  # < ansible 2.1
    BASECLASS = DEFAULT_MODULE.CallbackModule


reload(sys)
sys.setdefaultencoding('utf-8')


class CallbackModule(DEFAULT_MODULE.CallbackModule):

    """
    Ansible callback plugin
    """
    CALLBACK_VERSION = 2.2
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'openshift_quick_installer'
    CALLBACK_NEEDS_WHITELIST = False
    plays_count = 0
    plays_total_ran = 0

    def v2_playbook_on_start(self, playbook):
        """This is basically the start of it all"""
        self.plays_count = len(playbook.get_plays())
        self.plays_total_ran = 0

    def v2_playbook_on_play_start(self, play):
        """Each play calls this once before running any tasks

We could print the number of tasks here as well by using
`play.get_tasks()` but that is not accurate when a play includes a
role. Only the tasks directly assigned to a play are directly exposed
in the `play` object.

        """
        self.plays_total_ran += 1
        print("")
        print("Play %s/%s (%s)" % (self.plays_total_ran, self.plays_count, play.get_name()))

    # pylint: disable=unused-argument,no-self-use
    def v2_playbook_on_task_start(self, task, is_conditional):
        """This prints out the task header. For example:

TASK [openshift_facts : Ensure PyYaml is installed] ***...

Rather than print out all that for every task, we print a dot
character to indicate a task has been started.
        """
        sys.stdout.write('.')

    def v2_runner_on_ok(self, result):
        """This prints out task results in a fancy format"""
        pass

    def v2_runner_item_on_ok(self, result):
        """Print out task results for you're iterating"""
        pass

    def v2_runner_item_on_skipped(self, result):
        """Print out task results when an item is skipped"""
        pass

    def v2_runner_on_skipped(self, result):
        """Print out task results when a task (or something else?) is skipped"""
        pass

    def v2_playbook_on_notify(self, res, handler):
        """Printer for handlers

Rather than print out a header for every handler, we print a dot
character to indicate a handler task has been started.
        """
        sys.stdout.write('.')
