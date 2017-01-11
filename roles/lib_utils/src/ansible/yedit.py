# flake8: noqa
# pylint: skip-file


def get_curr_value(invalue, val_type):
    '''return the current value'''
    if invalue is None:
        return None

    curr_value = invalue
    if val_type == 'yaml':
        curr_value = yaml.load(invalue)
    elif val_type == 'json':
        curr_value = json.loads(invalue)

    return curr_value


def parse_value(inc_value, vtype=''):
    '''determine value type passed'''
    true_bools = ['y', 'Y', 'yes', 'Yes', 'YES', 'true', 'True', 'TRUE',
                  'on', 'On', 'ON', ]
    false_bools = ['n', 'N', 'no', 'No', 'NO', 'false', 'False', 'FALSE',
                   'off', 'Off', 'OFF']

    # It came in as a string but you didn't specify value_type as string
    # we will convert to bool if it matches any of the above cases
    if isinstance(inc_value, str) and 'bool' in vtype:
        if inc_value not in true_bools and inc_value not in false_bools:
            raise YeditException('Not a boolean type. str=[%s] vtype=[%s]'
                                 % (inc_value, vtype))
    elif isinstance(inc_value, bool) and 'str' in vtype:
        inc_value = str(inc_value)

    # If vtype is not str then go ahead and attempt to yaml load it.
    if isinstance(inc_value, str) and 'str' not in vtype:
        try:
            inc_value = yaml.load(inc_value)
        except Exception:
            raise YeditException('Could not determine type of incoming ' +
                                 'value. value=[%s] vtype=[%s]'
                                 % (type(inc_value), vtype))

    return inc_value


# pylint: disable=too-many-branches
def main():
    ''' ansible oc module for secrets '''

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', type='str',
                       choices=['present', 'absent', 'list']),
            debug=dict(default=False, type='bool'),
            src=dict(default=None, type='str'),
            content=dict(default=None),
            content_type=dict(default='dict', choices=['dict']),
            key=dict(default='', type='str'),
            value=dict(),
            value_type=dict(default='', type='str'),
            update=dict(default=False, type='bool'),
            append=dict(default=False, type='bool'),
            index=dict(default=None, type='int'),
            curr_value=dict(default=None, type='str'),
            curr_value_format=dict(default='yaml',
                                   choices=['yaml', 'json', 'str'],
                                   type='str'),
            backup=dict(default=True, type='bool'),
            separator=dict(default='.', type='str'),
        ),
        mutually_exclusive=[["curr_value", "index"], ['update', "append"]],
        required_one_of=[["content", "src"]],
    )

    rval = Yedit.run_ansible(module)
    if 'failed' in rval and rval['failed']:
        module.fail_json(msg=rval['msg'])

    module.exit_json(**rval)


if __name__ == '__main__':
    main()
