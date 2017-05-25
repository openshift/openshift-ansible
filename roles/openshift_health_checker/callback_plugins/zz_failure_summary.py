'''
Ansible callback plugin.
'''

# Reason: In several locations below we disable pylint protected-access
#         for Ansible objects that do not give us any public way
#         to access the full details we need to report check failures.
# Status: disabled permanently or until Ansible object has a public API.
# This does leave the code more likely to be broken by future Ansible changes.

from pprint import pformat

from ansible.plugins.callback import CallbackBase
from ansible import constants as C
from ansible.utils.color import stringc


class CallbackModule(CallbackBase):
    '''
    This callback plugin stores task results and summarizes failures.
    The file name is prefixed with `zz_` to make this plugin be loaded last by
    Ansible, thus making its output the last thing that users see.
    '''

    CALLBACK_VERSION = 2.0
    CALLBACK_TYPE = 'aggregate'
    CALLBACK_NAME = 'failure_summary'
    CALLBACK_NEEDS_WHITELIST = False
    _playbook_file = None

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.__failures = []

    def v2_playbook_on_start(self, playbook):
        super(CallbackModule, self).v2_playbook_on_start(playbook)
        # re: playbook attrs see top comment  # pylint: disable=protected-access
        self._playbook_file = playbook._file_name

    def v2_runner_on_failed(self, result, ignore_errors=False):
        super(CallbackModule, self).v2_runner_on_failed(result, ignore_errors)
        self.__failures.append(dict(result=result, ignore_errors=ignore_errors))

    def v2_playbook_on_stats(self, stats):
        super(CallbackModule, self).v2_playbook_on_stats(stats)
        if self.__failures:
            self._print_failure_details(self.__failures)

    def _print_failure_details(self, failures):
        '''Print a summary of failed tasks or checks.'''
        self._display.display(u'\nFailure summary:\n')

        width = len(str(len(failures)))
        initial_indent_format = u'  {{:>{width}}}. '.format(width=width)
        initial_indent_len = len(initial_indent_format.format(0))
        subsequent_indent = u' ' * initial_indent_len
        subsequent_extra_indent = u' ' * (initial_indent_len + 10)

        for i, failure in enumerate(failures, 1):
            entries = _format_failure(failure)
            self._display.display(u'\n{}{}'.format(initial_indent_format.format(i), entries[0]))
            for entry in entries[1:]:
                entry = entry.replace(u'\n', u'\n' + subsequent_extra_indent)
                indented = u'{}{}'.format(subsequent_indent, entry)
                self._display.display(indented)

        failed_checks = set()
        playbook_context = None
        # re: result attrs see top comment  # pylint: disable=protected-access
        for failure in failures:
            # get context from check task result since callback plugins cannot access task vars
            playbook_context = playbook_context or failure['result']._result.get('playbook_context')
            failed_checks.update(
                name
                for name, result in failure['result']._result.get('checks', {}).items()
                if result.get('failed')
            )
        if failed_checks:
            self._print_check_failure_summary(failed_checks, playbook_context)

    def _print_check_failure_summary(self, failed_checks, context):
        checks = ','.join(sorted(failed_checks))
        # NOTE: context is not set if all failures occurred prior to checks task
        summary = (
            '\n'
            'The execution of "{playbook}"\n'
            'includes checks designed to fail early if the requirements\n'
            'of the playbook are not met. One or more of these checks\n'
            'failed. To disregard these results, you may choose to\n'
            'disable failing checks by setting an Ansible variable:\n\n'
            '   openshift_disable_check={checks}\n\n'
            'Failing check names are shown in the failure details above.\n'
            'Some checks may be configurable by variables if your requirements\n'
            'are different from the defaults; consult check documentation.\n'
            'Variables can be set in the inventory or passed on the\n'
            'command line using the -e flag to ansible-playbook.\n'
        ).format(playbook=self._playbook_file, checks=checks)
        if context in ['pre-install', 'health']:
            summary = (
                '\n'
                'You may choose to configure or disable failing checks by\n'
                'setting Ansible variables. To disable those above:\n\n'
                '    openshift_disable_check={checks}\n\n'
                'Consult check documentation for configurable variables.\n'
                'Variables can be set in the inventory or passed on the\n'
                'command line using the -e flag to ansible-playbook.\n'
            ).format(checks=checks)
        # other expected contexts: install, upgrade
        self._display.display(summary)


# re: result attrs see top comment  # pylint: disable=protected-access
def _format_failure(failure):
    '''Return a list of pretty-formatted text entries describing a failure, including
    relevant information about it. Expect that the list of text entries will be joined
    by a newline separator when output to the user.'''
    result = failure['result']
    host = result._host.get_name()
    play = _get_play(result._task)
    if play:
        play = play.get_name()
    task = result._task.get_name()
    msg = result._result.get('msg', u'???')
    fields = (
        (u'Host', host),
        (u'Play', play),
        (u'Task', task),
        (u'Message', stringc(msg, C.COLOR_ERROR)),
    )
    if 'checks' in result._result:
        fields += ((u'Details', _format_failed_checks(result._result['checks'])),)
    row_format = '{:10}{}'
    return [row_format.format(header + u':', body) for header, body in fields]


def _format_failed_checks(checks):
    '''Return pretty-formatted text describing checks that failed.'''
    failed_check_msgs = []
    for check, body in checks.items():
        if body.get('failed', False):   # only show the failed checks
            msg = body.get('msg', u"Failed without returning a message")
            failed_check_msgs.append('check "%s":\n%s' % (check, msg))
    if failed_check_msgs:
        return stringc("\n\n".join(failed_check_msgs), C.COLOR_ERROR)
    else:    # something failed but no checks will admit to it, so dump everything
        return stringc(pformat(checks), C.COLOR_ERROR)


# This is inspired by ansible.playbook.base.Base.dump_me.
# re: play/task/block attrs see top comment  # pylint: disable=protected-access
def _get_play(obj):
    '''Given a task or block, recursively tries to find its parent play.'''
    if hasattr(obj, '_play'):
        return obj._play
    if getattr(obj, '_parent'):
        return _get_play(obj._parent)
