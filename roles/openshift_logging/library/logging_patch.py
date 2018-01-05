#!/usr/bin/python

""" Ansible module to help with creating context patch file with whitelisting for logging """

import difflib
import re

from ansible.module_utils.basic import AnsibleModule


DOCUMENTATION = '''
---
module: logging_patch

short_description: This will create a context patch file while giving ability
  to whitelist some lines (excluding them from comparison)

description:
    - "To create configmap patches for logging"

author:
    - Eric Wolinetz ewolinet@redhat.com
'''


EXAMPLES = '''
- logging_patch:
    original_file: "{{ tempdir }}/current.yml"
    new_file: "{{ configmap_new_file }}"
    whitelist: "{{ configmap_protected_lines | default([]) }}"

'''


def account_for_whitelist(file_contents, white_list=None):
    """ This method will remove lines that contain whitelist values from the content
        of the file so that we aren't build a patch based on that line

        Usage:

          for file_contents:

            index:
              number_of_shards: {{ es_number_of_shards | default ('1') }}
              number_of_replicas: {{ es_number_of_replicas | default ('0') }}
              unassigned.node_left.delayed_timeout: 2m
              translog:
                flush_threshold_size: 256mb
                flush_threshold_period: 5m


          and white_list:

            ['number_of_shards', 'number_of_replicas']


        We would end up with:

            index:
              unassigned.node_left.delayed_timeout: 2m
              translog:
                flush_threshold_size: 256mb
                flush_threshold_period: 5m

    """

    for line in white_list:
        file_contents = re.sub(r".*%s:.*\n" % line, "", file_contents)

    return file_contents


def run_module():
    """ The body of the module, we check if the variable name specified as the value
        for the key is defined. If it is then we use that value as for the original key """

    module = AnsibleModule(
        argument_spec=dict(
            original_file=dict(type='str', required=True),
            new_file=dict(type='str', required=True),
            whitelist=dict(required=False, type='list', default=[])
        ),
        supports_check_mode=True
    )

    original_fh = open(module.params['original_file'], "r")
    original_contents = original_fh.read()
    original_fh.close()

    original_contents = account_for_whitelist(original_contents, module.params['whitelist'])

    new_fh = open(module.params['new_file'], "r")
    new_contents = new_fh.read()
    new_fh.close()

    new_contents = account_for_whitelist(new_contents, module.params['whitelist'])

    uni_diff = difflib.unified_diff(new_contents.splitlines(),
                                    original_contents.splitlines(),
                                    lineterm='')

    return module.exit_json(changed=False,  # noqa: F405
                            raw_patch="\n".join(uni_diff))


def main():
    """ main """
    run_module()


if __name__ == '__main__':
    main()
