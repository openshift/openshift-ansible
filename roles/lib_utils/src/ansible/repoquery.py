# pylint: skip-file
# flake8: noqa


def main():
    '''
    ansible repoquery module
    '''
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='list', type='str', choices=['list']),
            name=dict(default=None, required=True, type='str'),
            query_type=dict(default='repos', required=False, type='str',
                            choices=[
                                'installed', 'available', 'recent',
                                'updates', 'extras', 'all', 'repos'
                            ]),
            verbose=dict(default=False, required=False, type='bool'),
            show_duplicates=dict(default=False, required=False, type='bool'),
            match_version=dict(default=None, required=False, type='str'),
            ignore_excluders=dict(default=False, required=False, type='bool'),
        ),
        supports_check_mode=False,
        required_if=[('show_duplicates', True, ['name'])],
    )

    rval = Repoquery.run_ansible(module.params, module.check_mode)

    if 'failed' in rval:
        module.fail_json(**rval)

    module.exit_json(**rval)


if __name__ == "__main__":
    main()
