# pylint: disable=invalid-name,protected-access,import-error,line-too-long,attribute-defined-outside-init

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

"""This file is a stdout callback plugin for the OpenShift Quick
Installer. The purpose of this callback plugin is to reduce the amount
of produced output for customers and enable simpler progress checking.

What's different:

* Playbook progress is expressed as: Play <current_play>/<total_plays> (Play Name)
  Ex: Play 3/30 (Initialize Megafrobber)

* The Tasks and Handlers in each play (and included roles) are printed
  as a series of .'s following the play progress line.

* Many of these methods include copy and paste code from the upstream
  default.py callback. We do that to give us control over the stdout
  output while allowing Ansible to handle the file logging
  normally. The biggest changes here are that we are manually setting
  `log_only` to True in the Display.display method and we redefine the
  Display.banner method locally so we can set log_only on that call as
  well.

"""

from __future__ import (absolute_import, print_function)
import sys
from ansible import constants as C
from ansible.plugins.callback import CallbackBase
from ansible.utils.color import colorize, hostcolor


class CallbackModule(CallbackBase):

    """
    Ansible callback plugin
    """
    CALLBACK_VERSION = 2.2
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'openshift_quick_installer'
    CALLBACK_NEEDS_WHITELIST = False
    plays_count = 0
    plays_total_ran = 0

    def __init__(self):
        """Constructor, ensure standard self.*s are set"""
        self._play = None
        self._last_task_banner = None
        super(CallbackModule, self).__init__()

    def banner(self, msg, color=None):
        '''Prints a header-looking line with stars taking up to 80 columns
        of width (3 columns, minimum)

        Overrides the upstream banner method so that display is called
        with log_only=True
        '''
        msg = msg.strip()
        star_len = (79 - len(msg))
        if star_len < 0:
            star_len = 3
        stars = "*" * star_len
        self._display.display("\n%s %s" % (msg, stars), color=color, log_only=True)

    def _print_task_banner(self, task):
        """Imported from the upstream 'default' callback"""
        # args can be specified as no_log in several places: in the task or in
        # the argument spec.  We can check whether the task is no_log but the
        # argument spec can't be because that is only run on the target
        # machine and we haven't run it thereyet at this time.
        #
        # So we give people a config option to affect display of the args so
        # that they can secure this if they feel that their stdout is insecure
        # (shoulder surfing, logging stdout straight to a file, etc).
        args = ''
        if not task.no_log and C.DISPLAY_ARGS_TO_STDOUT:
            args = ', '.join('%s=%s' % a for a in task.args.items())
            args = ' %s' % args

        self.banner(u"TASK [%s%s]" % (task.get_name().strip(), args))
        if self._display.verbosity >= 2:
            path = task.get_path()
            if path:
                self._display.display(u"task path: %s" % path, color=C.COLOR_DEBUG, log_only=True)

        self._last_task_banner = task._uuid

    def v2_playbook_on_start(self, playbook):
        """This is basically the start of it all"""
        self.plays_count = len(playbook.get_plays())
        self.plays_total_ran = 0

        if self._display.verbosity > 1:
            from os.path import basename
            self.banner("PLAYBOOK: %s" % basename(playbook._file_name))

    def v2_playbook_on_play_start(self, play):
        """Each play calls this once before running any tasks

We could print the number of tasks here as well by using
`play.get_tasks()` but that is not accurate when a play includes a
role. Only the tasks directly assigned to a play are exposed in the
`play` object.
        """
        self.plays_total_ran += 1
        print("")
        print("Play %s/%s (%s)" % (self.plays_total_ran, self.plays_count, play.get_name()))

        name = play.get_name().strip()
        if not name:
            msg = "PLAY"
        else:
            msg = "PLAY [%s]" % name

        self._play = play

        self.banner(msg)

    # pylint: disable=unused-argument,no-self-use
    def v2_playbook_on_task_start(self, task, is_conditional):
        """This prints out the task header. For example:

TASK [openshift_facts : Ensure PyYaml is installed] ***...

Rather than print out all that for every task, we print a dot
character to indicate a task has been started.
        """
        sys.stdout.write('.')

        args = ''
        # args can be specified as no_log in several places: in the task or in
        # the argument spec.  We can check whether the task is no_log but the
        # argument spec can't be because that is only run on the target
        # machine and we haven't run it thereyet at this time.
        #
        # So we give people a config option to affect display of the args so
        # that they can secure this if they feel that their stdout is insecure
        # (shoulder surfing, logging stdout straight to a file, etc).
        if not task.no_log and C.DISPLAY_ARGS_TO_STDOUT:
            args = ', '.join(('%s=%s' % a for a in task.args.items()))
            args = ' %s' % args
        self.banner("TASK [%s%s]" % (task.get_name().strip(), args))
        if self._display.verbosity >= 2:
            path = task.get_path()
            if path:
                self._display.display("task path: %s" % path, color=C.COLOR_DEBUG, log_only=True)

    # pylint: disable=unused-argument,no-self-use
    def v2_playbook_on_handler_task_start(self, task):
        """Print out task header for handlers

Rather than print out a header for every handler, we print a dot
character to indicate a handler task has been started.
"""
        sys.stdout.write('.')

        self.banner("RUNNING HANDLER [%s]" % task.get_name().strip())

    # pylint: disable=unused-argument,no-self-use
    def v2_playbook_on_cleanup_task_start(self, task):
        """Print out a task header for cleanup tasks

Rather than print out a header for every handler, we print a dot
character to indicate a handler task has been started.
"""
        sys.stdout.write('.')

        self.banner("CLEANUP TASK [%s]" % task.get_name().strip())

    def v2_playbook_on_include(self, included_file):
        """Print out paths to statically included files"""
        msg = 'included: %s for %s' % (included_file._filename, ", ".join([h.name for h in included_file._hosts]))
        self._display.display(msg, color=C.COLOR_SKIP, log_only=True)

    def v2_runner_on_ok(self, result):
        """This prints out task results in a fancy format

The only thing we change here is adding `log_only=True` to the
.display() call
        """
        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        self._clean_results(result._result, result._task.action)
        if result._task.action in ('include', 'import_role'):
            return
        elif result._result.get('changed', False):
            if delegated_vars:
                msg = "changed: [%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
            else:
                msg = "changed: [%s]" % result._host.get_name()
            color = C.COLOR_CHANGED
        else:
            if delegated_vars:
                msg = "ok: [%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
            else:
                msg = "ok: [%s]" % result._host.get_name()
            color = C.COLOR_OK

        if result._task.loop and 'results' in result._result:
            self._process_items(result)
        else:

            if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and '_ansible_verbose_override' not in result._result:
                msg += " => %s" % (self._dump_results(result._result),)
            self._display.display(msg, color=color, log_only=True)

        self._handle_warnings(result._result)

    def v2_runner_item_on_ok(self, result):
        """Print out task results for items you're iterating over"""
        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        if result._task.action in ('include', 'import_role'):
            return
        elif result._result.get('changed', False):
            msg = 'changed'
            color = C.COLOR_CHANGED
        else:
            msg = 'ok'
            color = C.COLOR_OK

        if delegated_vars:
            msg += ": [%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
        else:
            msg += ": [%s]" % result._host.get_name()

        msg += " => (item=%s)" % (self._get_item(result._result),)

        if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and '_ansible_verbose_override' not in result._result:
            msg += " => %s" % self._dump_results(result._result)
        self._display.display(msg, color=color, log_only=True)

    def v2_runner_item_on_skipped(self, result):
        """Print out task results when an item is skipped"""
        if C.DISPLAY_SKIPPED_HOSTS:
            msg = "skipping: [%s] => (item=%s) " % (result._host.get_name(), self._get_item(result._result))
            if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and '_ansible_verbose_override' not in result._result:
                msg += " => %s" % self._dump_results(result._result)
            self._display.display(msg, color=C.COLOR_SKIP, log_only=True)

    def v2_runner_on_skipped(self, result):
        """Print out task results when a task (or something else?) is skipped"""
        if C.DISPLAY_SKIPPED_HOSTS:
            if result._task.loop and 'results' in result._result:
                self._process_items(result)
            else:
                msg = "skipping: [%s]" % result._host.get_name()
                if (self._display.verbosity > 0 or '_ansible_verbose_always' in result._result) and '_ansible_verbose_override' not in result._result:
                    msg += " => %s" % self._dump_results(result._result)
                self._display.display(msg, color=C.COLOR_SKIP, log_only=True)

    def v2_playbook_on_notify(self, res, handler):
        """What happens when a task result is 'changed' and the task has a
'notify' list attached.
        """
        self._display.display("skipping: no hosts matched", color=C.COLOR_SKIP, log_only=True)

    ######################################################################
    # So we can bubble up errors to the top
    def v2_runner_on_failed(self, result, ignore_errors=False):
        """I guess this is when an entire task has failed?"""

        if self._play.strategy == 'free' and self._last_task_banner != result._task._uuid:
            self._print_task_banner(result._task)

        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        if 'exception' in result._result:
            if self._display.verbosity < 3:
                # extract just the actual error message from the exception text
                error = result._result['exception'].strip().split('\n')[-1]
                msg = "An exception occurred during task execution. To see the full traceback, use -vvv. The error was: %s" % error
            else:
                msg = "An exception occurred during task execution. The full traceback is:\n" + result._result['exception']

            self._display.display(msg, color=C.COLOR_ERROR)

        if result._task.loop and 'results' in result._result:
            self._process_items(result)

        else:
            if delegated_vars:
                self._display.display("fatal: [%s -> %s]: FAILED! => %s" % (result._host.get_name(), delegated_vars['ansible_host'], self._dump_results(result._result)), color=C.COLOR_ERROR)
            else:
                self._display.display("fatal: [%s]: FAILED! => %s" % (result._host.get_name(), self._dump_results(result._result)), color=C.COLOR_ERROR)

        if ignore_errors:
            self._display.display("...ignoring", color=C.COLOR_SKIP)

    def v2_runner_item_on_failed(self, result):
        """When an item in a task fails."""
        delegated_vars = result._result.get('_ansible_delegated_vars', None)
        if 'exception' in result._result:
            if self._display.verbosity < 3:
                # extract just the actual error message from the exception text
                error = result._result['exception'].strip().split('\n')[-1]
                msg = "An exception occurred during task execution. To see the full traceback, use -vvv. The error was: %s" % error
            else:
                msg = "An exception occurred during task execution. The full traceback is:\n" + result._result['exception']

            self._display.display(msg, color=C.COLOR_ERROR)

        msg = "failed: "
        if delegated_vars:
            msg += "[%s -> %s]" % (result._host.get_name(), delegated_vars['ansible_host'])
        else:
            msg += "[%s]" % (result._host.get_name())

        self._display.display(msg + " (item=%s) => %s" % (self._get_item(result._result), self._dump_results(result._result)), color=C.COLOR_ERROR)
        self._handle_warnings(result._result)

    ######################################################################
    def v2_playbook_on_stats(self, stats):
        """Print the final playbook run stats"""
        self._display.display("", screen_only=True)
        self.banner("PLAY RECAP")

        hosts = sorted(stats.processed.keys())
        for h in hosts:
            t = stats.summarize(h)

            self._display.display(
                u"%s : %s %s %s %s" % (
                    hostcolor(h, t),
                    colorize(u'ok', t['ok'], C.COLOR_OK),
                    colorize(u'changed', t['changed'], C.COLOR_CHANGED),
                    colorize(u'unreachable', t['unreachable'], C.COLOR_UNREACHABLE),
                    colorize(u'failed', t['failures'], C.COLOR_ERROR)),
                screen_only=True
            )

            self._display.display(
                u"%s : %s %s %s %s" % (
                    hostcolor(h, t, False),
                    colorize(u'ok', t['ok'], None),
                    colorize(u'changed', t['changed'], None),
                    colorize(u'unreachable', t['unreachable'], None),
                    colorize(u'failed', t['failures'], None)),
                log_only=True
            )

        self._display.display("", screen_only=True)
        self._display.display("", screen_only=True)

        # Some plays are conditional and won't run (such as load
        # balancers) if they aren't required. Sometimes plays are
        # conditionally included later in the run. Let the user know
        # about this to avoid potential confusion.
        if self.plays_total_ran != self.plays_count:
            print("Installation Complete: Note: Play count is only an estimate, some plays may have been skipped or dynamically added")
            self._display.display("", screen_only=True)
