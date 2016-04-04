#pylint: skip-file

def main():
    '''
    ansible oc module for secrets
    '''

    module = AnsibleModule(
        argument_spec=dict(
            state=dict(default='present', type='str',
                       choices=['present', 'absent', 'list']),
            debug=dict(default=False, type='bool'),
            src=dict(default=None, type='str'),
            content=dict(default=None, type='dict'),
            key=dict(default=None, type='str'),
            value=dict(default=None, type='str'),
            value_format=dict(default='yaml', choices=['yaml', 'json'], type='str'),
        ),
        #mutually_exclusive=[["src", "content"]],

        supports_check_mode=True,
    )
    state = module.params['state']

    yamlfile = Yedit(module.params['src'], module.params['content'])

    rval = yamlfile.load()
    if not rval and state != 'present':
        module.fail_json(msg='Error opening file [%s].  Verify that the' + \
                             ' file exists, that it is has correct permissions, and is valid yaml.')

    if state == 'list':
        module.exit_json(changed=False, results=rval, state="list")

    if state == 'absent':
        rval = yamlfile.delete(module.params['key'])
        module.exit_json(changed=rval[0], results=rval[1], state="absent")

    if state == 'present':

        if module.params['value_format'] == 'yaml':
            value = yaml.load(module.params['value'])
        elif module.params['value_format'] == 'json':
            value = json.loads(module.params['value'])

        if rval:
            rval = yamlfile.put(module.params['key'], value)
            if rval[0]:
                yamlfile.write()
            module.exit_json(changed=rval[0], results=rval[1], state="present")

        if not module.params['content']:
            rval = yamlfile.create(module.params['key'], value)
        else:
            rval = yamlfile.load()
        yamlfile.write()

        module.exit_json(changed=rval[0], results=rval[1], state="present")

    module.exit_json(failed=True,
                     changed=False,
                     results='Unknown state passed. %s' % state,
                     state="unknown")

# pylint: disable=redefined-builtin, unused-wildcard-import, wildcard-import, locally-disabled
# import module snippets.  This are required
from ansible.module_utils.basic import *

main()
