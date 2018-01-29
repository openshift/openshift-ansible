#!/usr/bin/python

""" Ansible module to help with setting facts conditionally based on other facts """

from ansible.module_utils.basic import AnsibleModule


DOCUMENTATION = '''
---
module: conditional_set_fact

short_description: This will set a fact if the value is defined

description:
    - "To avoid constant set_fact & when conditions for each var we can use this"

author:
    - Eric Wolinetz ewolinet@redhat.com
'''


EXAMPLES = '''
- name: Conditionally set fact
  conditional_set_fact:
    fact1: not_defined_variable

- name: Conditionally set fact
  conditional_set_fact:
    fact1: not_defined_variable
    fact2: defined_variable

- name: Conditionally set fact falling back on default
  conditional_set_fact:
    fact1: not_defined_var | defined_variable

'''


def run_module():
    """ The body of the module, we check if the variable name specified as the value
        for the key is defined. If it is then we use that value as for the original key """

    module = AnsibleModule(
        argument_spec=dict(
            facts=dict(type='dict', required=True),
            vars=dict(required=False, type='dict', default=[])
        ),
        supports_check_mode=True
    )

    local_facts = dict()
    is_changed = False

    for param in module.params['vars']:
        other_vars = module.params['vars'][param].replace(" ", "")

        for other_var in other_vars.split('|'):
            if other_var in module.params['facts']:
                local_facts[param] = module.params['facts'][other_var]
                if not is_changed:
                    is_changed = True
                break

    return module.exit_json(changed=is_changed,  # noqa: F405
                            ansible_facts=local_facts)


def main():
    """ main """
    run_module()


if __name__ == '__main__':
    main()
