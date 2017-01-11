'''Plugin to override the default output logic.'''

# upstream: https://gist.github.com/cliffano/9868180

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


# For some reason this has to be done
import imp
import os

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


class CallbackModule(DEFAULT_MODULE.CallbackModule):  # pylint: disable=too-few-public-methods,no-init
    '''
    Override for the default callback module.

    Render std err/out outside of the rest of the result which it prints with
    indentation.
    '''
    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'stdout'
    CALLBACK_NAME = 'default'

    def __init__(self, *args, **kwargs):
        # pylint: disable=non-parent-init-called
        BASECLASS.__init__(self, *args, **kwargs)

    def _dump_results(self, result):
        '''Return the text to output for a result.'''
        result['_ansible_verbose_always'] = True

        save = {}
        for key in ['stdout', 'stdout_lines', 'stderr', 'stderr_lines', 'msg']:
            if key in result:
                save[key] = result.pop(key)

        output = BASECLASS._dump_results(self, result)  # pylint: disable=protected-access

        for key in ['stdout', 'stderr', 'msg']:
            if key in save and save[key]:
                output += '\n\n%s:\n\n%s\n' % (key.upper(), save[key])

        for key, value in save.items():
            result[key] = value

        return output
