# vim: expandtab:tabstop=4:shiftwidth=4
'''
Ansible callback plugin.
'''

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

    def __init__(self):
        super(CallbackModule, self).__init__()
        self.__failures = []

    def v2_runner_on_failed(self, result, ignore_errors=False):
        super(CallbackModule, self).v2_runner_on_failed(result, ignore_errors)
        self.__failures.append(dict(result=result, ignore_errors=ignore_errors))

    def v2_playbook_on_stats(self, stats):
        super(CallbackModule, self).v2_playbook_on_stats(stats)
        # TODO: update condition to consider a host var or env var to
        # enable/disable the summary, so that we can control the output from a
        # play.
        if self.__failures:
            self._print_failure_summary()

    def _print_failure_summary(self):
        '''Print a summary of failed tasks (including ignored failures).'''
        self._display.display(u'\nFailure summary:\n')

        # TODO: group failures by host or by task. If grouped by host, it is
        # easy to see all problems of a given host. If grouped by task, it is
        # easy to see what hosts needs the same fix.

        width = len(str(len(self.__failures)))
        initial_indent_format = u'  {{:>{width}}}. '.format(width=width)
        initial_indent_len = len(initial_indent_format.format(0))
        subsequent_indent = u' ' * initial_indent_len
        subsequent_extra_indent = u' ' * (initial_indent_len + 10)

        for i, failure in enumerate(self.__failures, 1):
            lines = _format_failure(failure)
            self._display.display(u'\n{}{}'.format(initial_indent_format.format(i), lines[0]))
            for line in lines[1:]:
                line = line.replace(u'\n', u'\n' + subsequent_extra_indent)
                indented = u'{}{}'.format(subsequent_indent, line)
                self._display.display(indented)


# Reason: disable pylint protected-access because we need to access _*
#         attributes of a task result to implement this method.
# Status: permanently disabled unless Ansible's API changes.
# pylint: disable=protected-access
def _format_failure(failure):
    '''Return a list of pretty-formatted lines describing a failure, including
    relevant information about it. Line separators are not included.'''
    result = failure['result']
    host = result._host.get_name()
    play = _get_play(result._task)
    if play:
        play = play.get_name()
    task = result._task.get_name()
    msg = result._result.get('msg', u'???')
    rows = (
        (u'Host', host),
        (u'Play', play),
        (u'Task', task),
        (u'Message', stringc(msg, C.COLOR_ERROR)),
    )
    row_format = '{:10}{}'
    return [row_format.format(header + u':', body) for header, body in rows]


# Reason: disable pylint protected-access because we need to access _*
#         attributes of obj to implement this function.
#         This is inspired by ansible.playbook.base.Base.dump_me.
# Status: permanently disabled unless Ansible's API changes.
# pylint: disable=protected-access
def _get_play(obj):
    '''Given a task or block, recursively tries to find its parent play.'''
    if hasattr(obj, '_play'):
        return obj._play
    if getattr(obj, '_parent'):
        return _get_play(obj._parent)
