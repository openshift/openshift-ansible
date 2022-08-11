#!/usr/bin/python
# -*- coding: utf-8 -*-

# Copyright: (c) 2012, Jan-Piet Mens <jpmens () gmail.com>
# Copyright: (c) 2015, Ales Nosek <anosek.nosek () gmail.com>
# Copyright: (c) 2017, Ansible Project
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)

from __future__ import absolute_import, division, print_function
__metaclass__ = type


DOCUMENTATION = r'''
---
module: ini_file
short_description: Tweak settings in INI files
extends_documentation_fragment: files
description:
     - Manage (add, remove, change) individual settings in an INI-style file without having
       to manage the file as a whole with, say, M(ansible.builtin.template) or M(ansible.builtin.assemble).
     - Adds missing sections if they don't exist.
     - Before Ansible 2.0, comments are discarded when the source file is read, and therefore will not show up in the destination file.
     - Since Ansible 2.3, this module adds missing ending newlines to files to keep in line with the POSIX standard, even when
       no other modifications need to be applied.
options:
  path:
    description:
      - Path to the INI-style file; this file is created if required.
      - Before Ansible 2.3 this option was only usable as I(dest).
    type: path
    required: true
    aliases: [ dest ]
  section:
    description:
      - Section name in INI file. This is added if C(state=present) automatically when
        a single value is being set.
      - If left empty or set to C(null), the I(option) will be placed before the first I(section).
      - Using C(null) is also required if the config format does not support sections.
    type: str
    required: true
  option:
    description:
      - If set (required for changing a I(value)), this is the name of the option.
      - May be omitted if adding/removing a whole I(section).
    type: str
  value:
    description:
      - The string value to be associated with an I(option).
      - May be omitted when removing an I(option).
      - Mutually exclusive with I(values).
      - I(value=v) is equivalent to I(values=[v]).
    type: str
  values:
    description:
      - The string value to be associated with an I(option).
      - May be omitted when removing an I(option).
      - Mutually exclusive with I(value).
      - I(value=v) is equivalent to I(values=[v]).
    type: list
    elements: str
    version_added: 3.6.0
  backup:
    description:
      - Create a backup file including the timestamp information so you can get
        the original file back if you somehow clobbered it incorrectly.
    type: bool
    default: no
  state:
    description:
      - If set to C(absent) and I(exclusive) set to C(yes) all matching I(option) lines are removed.
      - If set to C(absent) and I(exclusive) set to C(no) the specified C(option=value) lines are removed,
        but the other I(option)s with the same name are not touched.
      - If set to C(present) and I(exclusive) set to C(no) the specified C(option=values) lines are added,
        but the other I(option)s with the same name are not touched.
      - If set to C(present) and I(exclusive) set to C(yes) all given C(option=values) lines will be
        added and the other I(option)s with the same name are removed.
    type: str
    choices: [ absent, present ]
    default: present
  exclusive:
    description:
      - If set to C(yes) (default), all matching I(option) lines are removed when I(state=absent),
        or replaced when I(state=present).
      - If set to C(no), only the specified I(value(s)) are added when I(state=present),
        or removed when I(state=absent), and existing ones are not modified.
    type: bool
    default: yes
    version_added: 3.6.0
  no_extra_spaces:
    description:
      - Do not insert spaces before and after '=' symbol.
    type: bool
    default: no
  create:
    description:
      - If set to C(no), the module will fail if the file does not already exist.
      - By default it will create the file if it is missing.
    type: bool
    default: yes
  allow_no_value:
    description:
      - Allow option without value and without '=' symbol.
    type: bool
    default: no
notes:
   - While it is possible to add an I(option) without specifying a I(value), this makes no sense.
   - As of Ansible 2.3, the I(dest) option has been changed to I(path) as default, but I(dest) still works as well.
   - As of community.general 3.2.0, UTF-8 BOM markers are discarded when reading files.
author:
    - Jan-Piet Mens (@jpmens)
    - Ales Nosek (@noseka1)
'''

EXAMPLES = r'''
# Before Ansible 2.3, option 'dest' was used instead of 'path'
- name: Ensure "fav=lemonade is in section "[drinks]" in specified file
  community.general.ini_file:
    path: /etc/conf
    section: drinks
    option: fav
    value: lemonade
    mode: '0600'
    backup: yes

- name: Ensure "temperature=cold is in section "[drinks]" in specified file
  community.general.ini_file:
    path: /etc/anotherconf
    section: drinks
    option: temperature
    value: cold
    backup: yes

- name: Add "beverage=lemon juice" is in section "[drinks]" in specified file
  community.general.ini_file:
    path: /etc/conf
    section: drinks
    option: beverage
    value: lemon juice
    mode: '0600'
    state: present
    exclusive: no

- name: Ensure multiple values "beverage=coke" and "beverage=pepsi" are in section "[drinks]" in specified file
  community.general.ini_file:
    path: /etc/conf
    section: drinks
    option: beverage
    values:
      - coke
      - pepsi
    mode: '0600'
    state: present
'''

import io
import os
import re
import tempfile
import traceback

from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.common.text.converters import to_bytes, to_text


def match_opt(option, line):
    option = re.escape(option)
    return re.match('[#;]?( |\t)*(%s)( |\t)*(=|$)( |\t)*(.*)' % option, line)


def match_active_opt(option, line):
    option = re.escape(option)
    return re.match('( |\t)*(%s)( |\t)*(=|$)( |\t)*(.*)' % option, line)


def update_section_line(changed, section_lines, index, changed_lines, newline, msg):
    option_changed = section_lines[index] != newline
    changed = changed or option_changed
    if option_changed:
        msg = 'option changed'
    section_lines[index] = newline
    changed_lines[index] = 1
    return (changed, msg)


def do_ini(module, filename, section=None, option=None, values=None,
           state='present', exclusive=True, backup=False, no_extra_spaces=False,
           create=True, allow_no_value=False):

    if section is not None:
        section = to_text(section)
    if option is not None:
        option = to_text(option)

    # deduplicate entries in values
    values_unique = []
    [values_unique.append(to_text(value)) for value in values if value not in values_unique and value is not None]
    values = values_unique

    diff = dict(
        before='',
        after='',
        before_header='%s (content)' % filename,
        after_header='%s (content)' % filename,
    )

    if not os.path.exists(filename):
        if not create:
            module.fail_json(rc=257, msg='Destination %s does not exist!' % filename)
        destpath = os.path.dirname(filename)
        if not os.path.exists(destpath) and not module.check_mode:
            os.makedirs(destpath)
        ini_lines = []
    else:
        with io.open(filename, 'r', encoding="utf-8-sig") as ini_file:
            ini_lines = [to_text(line) for line in ini_file.readlines()]

    if module._diff:
        diff['before'] = u''.join(ini_lines)

    changed = False

    # ini file could be empty
    if not ini_lines:
        ini_lines.append(u'\n')

    # last line of file may not contain a trailing newline
    if ini_lines[-1] == u"" or ini_lines[-1][-1] != u'\n':
        ini_lines[-1] += u'\n'
        changed = True

    # append fake section lines to simplify the logic
    # At top:
    # Fake random section to do not match any other in the file
    # Using commit hash as fake section name
    fake_section_name = u"ad01e11446efb704fcdbdb21f2c43757423d91c5"

    # Insert it at the beginning
    ini_lines.insert(0, u'[%s]' % fake_section_name)

    # At bottom:
    ini_lines.append(u'[')

    # If no section is defined, fake section is used
    if not section:
        section = fake_section_name

    within_section = not section
    section_start = section_end = 0
    msg = 'OK'
    if no_extra_spaces:
        assignment_format = u'%s=%s\n'
    else:
        assignment_format = u'%s = %s\n'

    option_no_value_present = False

    non_blank_non_comment_pattern = re.compile(to_text(r'^[ \t]*([#;].*)?$'))

    before = after = []
    section_lines = []

    for index, line in enumerate(ini_lines):
        # find start and end of section
        if line.startswith(u'[%s]' % section):
            within_section = True
            section_start = index
        elif line.startswith(u'['):
            if within_section:
                section_end = index
                break

    before = ini_lines[0:section_start]
    section_lines = ini_lines[section_start:section_end]
    after = ini_lines[section_end:len(ini_lines)]

    # Keep track of changed section_lines
    changed_lines = [0] * len(section_lines)

    # handling multiple instances of option=value when state is 'present' with/without exclusive is a bit complex
    #
    # 1. edit all lines where we have a option=value pair with a matching value in values[]
    # 2. edit all the remaing lines where we have a matching option
    # 3. delete remaining lines where we have a matching option
    # 4. insert missing option line(s) at the end of the section

    if state == 'present' and option:
        for index, line in enumerate(section_lines):
            if match_opt(option, line):
                match = match_opt(option, line)
                if values and match.group(6) in values:
                    matched_value = match.group(6)
                    if not matched_value and allow_no_value:
                        # replace existing option with no value line(s)
                        newline = u'%s\n' % option
                        option_no_value_present = True
                    else:
                        # replace existing option=value line(s)
                        newline = assignment_format % (option, matched_value)
                    (changed, msg) = update_section_line(changed, section_lines, index, changed_lines, newline, msg)
                    values.remove(matched_value)
                elif not values and allow_no_value:
                    # replace existing option with no value line(s)
                    newline = u'%s\n' % option
                    (changed, msg) = update_section_line(changed, section_lines, index, changed_lines, newline, msg)
                    option_no_value_present = True
                    break

    if state == 'present' and exclusive and not allow_no_value:
        # override option with no value to option with value if not allow_no_value
        if len(values) > 0:
            for index, line in enumerate(section_lines):
                if not changed_lines[index] and match_active_opt(option, section_lines[index]):
                    newline = assignment_format % (option, values.pop(0))
                    (changed, msg) = update_section_line(changed, section_lines, index, changed_lines, newline, msg)
                    if len(values) == 0:
                        break
        # remove all remaining option occurrences from the rest of the section
        for index in range(len(section_lines) - 1, 0, -1):
            if not changed_lines[index] and match_active_opt(option, section_lines[index]):
                del section_lines[index]
                del changed_lines[index]
                changed = True
                msg = 'option changed'

    if state == 'present':
        # insert missing option line(s) at the end of the section
        for index in range(len(section_lines), 0, -1):
            # search backwards for previous non-blank or non-comment line
            if not non_blank_non_comment_pattern.match(section_lines[index - 1]):
                if option and values:
                    # insert option line(s)
                    for element in values[::-1]:
                        # items are added backwards, so traverse the list backwards to not confuse the user
                        # otherwise some of their options might appear in reverse order for whatever fancy reason ¯\_(ツ)_/¯
                        if element is not None:
                            # insert option=value line
                            section_lines.insert(index, assignment_format % (option, element))
                            msg = 'option added'
                            changed = True
                        elif element is None and allow_no_value:
                            # insert option with no value line
                            section_lines.insert(index, u'%s\n' % option)
                            msg = 'option added'
                            changed = True
                elif option and not values and allow_no_value and not option_no_value_present:
                    # insert option with no value line(s)
                    section_lines.insert(index, u'%s\n' % option)
                    msg = 'option added'
                    changed = True
                break

    if state == 'absent':
        if option:
            if exclusive:
                # delete all option line(s) with given option and ignore value
                new_section_lines = [line for line in section_lines if not (match_active_opt(option, line))]
                if section_lines != new_section_lines:
                    changed = True
                    msg = 'option changed'
                    section_lines = new_section_lines
            elif not exclusive and len(values) > 0:
                # delete specified option=value line(s)
                new_section_lines = [i for i in section_lines if not (match_active_opt(option, i) and match_active_opt(option, i).group(6) in values)]
                if section_lines != new_section_lines:
                    changed = True
                    msg = 'option changed'
                    section_lines = new_section_lines
        else:
            # drop the entire section
            if section_lines:
                section_lines = []
                msg = 'section removed'
                changed = True

    # reassemble the ini_lines after manipulation
    ini_lines = before + section_lines + after

    # remove the fake section line
    del ini_lines[0]
    del ini_lines[-1:]

    if not within_section and state == 'present':
        ini_lines.append(u'[%s]\n' % section)
        msg = 'section and option added'
        if option and values:
            for value in values:
                ini_lines.append(assignment_format % (option, value))
        elif option and not values and allow_no_value:
            ini_lines.append(u'%s\n' % option)
        else:
            msg = 'only section added'
        changed = True

    if module._diff:
        diff['after'] = u''.join(ini_lines)

    backup_file = None
    if changed and not module.check_mode:
        if backup:
            backup_file = module.backup_local(filename)

        encoded_ini_lines = [to_bytes(line) for line in ini_lines]
        try:
            tmpfd, tmpfile = tempfile.mkstemp(dir=module.tmpdir)
            f = os.fdopen(tmpfd, 'wb')
            f.writelines(encoded_ini_lines)
            f.close()
        except IOError:
            module.fail_json(msg="Unable to create temporary file %s", traceback=traceback.format_exc())

        try:
            module.atomic_move(tmpfile, filename)
        except IOError:
            module.ansible.fail_json(msg='Unable to move temporary \
                                   file %s to %s, IOError' % (tmpfile, filename), traceback=traceback.format_exc())

    return (changed, backup_file, diff, msg)


def main():

    module = AnsibleModule(
        argument_spec=dict(
            path=dict(type='path', required=True, aliases=['dest']),
            section=dict(type='str', required=True),
            option=dict(type='str'),
            value=dict(type='str'),
            values=dict(type='list', elements='str'),
            backup=dict(type='bool', default=False),
            state=dict(type='str', default='present', choices=['absent', 'present']),
            exclusive=dict(type='bool', default=True),
            no_extra_spaces=dict(type='bool', default=False),
            allow_no_value=dict(type='bool', default=False),
            create=dict(type='bool', default=True)
        ),
        mutually_exclusive=[
            ['value', 'values']
        ],
        add_file_common_args=True,
        supports_check_mode=True,
    )

    path = module.params['path']
    section = module.params['section']
    option = module.params['option']
    value = module.params['value']
    values = module.params['values']
    state = module.params['state']
    exclusive = module.params['exclusive']
    backup = module.params['backup']
    no_extra_spaces = module.params['no_extra_spaces']
    allow_no_value = module.params['allow_no_value']
    create = module.params['create']

    if state == 'present' and not allow_no_value and value is None and not values:
        module.fail_json(msg="Parameter 'value(s)' must be defined if state=present and allow_no_value=False.")

    if value is not None:
        values = [value]
    elif values is None:
        values = []

    (changed, backup_file, diff, msg) = do_ini(module, path, section, option, values, state, exclusive, backup, no_extra_spaces, create, allow_no_value)

    if not module.check_mode and os.path.exists(path):
        file_args = module.load_file_common_arguments(module.params)
        changed = module.set_fs_attributes_if_different(file_args, changed)

    results = dict(
        changed=changed,
        diff=diff,
        msg=msg,
        path=path,
    )
    if backup_file is not None:
        results['backup_file'] = backup_file

    # Mission complete
    module.exit_json(**results)


if __name__ == '__main__':
    main()
