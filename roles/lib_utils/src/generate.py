#!/usr/bin/env python
'''
  Generate the openshift-ansible/roles/lib_openshift_cli/library/ modules.
'''

import argparse
import os
import six
import yaml

OPENSHIFT_ANSIBLE_PATH = os.path.dirname(os.path.realpath(__file__))
OPENSHIFT_ANSIBLE_SOURCES_PATH = os.path.join(OPENSHIFT_ANSIBLE_PATH, 'sources.yml')  # noqa: E501


class GenerateAnsibleException(Exception):
    '''General Exception for generate function'''
    pass


def parse_args():
    '''parse arguments to generate'''
    parser = argparse.ArgumentParser(description="Generate ansible modules.")
    parser.add_argument('--verify', action='store_true', default=False,
                        help='Verify library code matches the generated code.')

    return parser.parse_args()


def generate(parts):
    '''generate the source code for the ansible modules'''

    data = six.StringIO()
    for fpart in parts:
        # first line is pylint disable so skip it
        with open(os.path.join(OPENSHIFT_ANSIBLE_PATH, fpart)) as pfd:
            for idx, line in enumerate(pfd):
                if idx in [0, 1] and 'flake8: noqa' in line or 'pylint: skip-file' in line:  # noqa: E501
                    continue

                data.write(line)

    return data


def main():
    ''' combine the necessary files to create the ansible module '''
    args = parse_args()

    library = os.path.join(OPENSHIFT_ANSIBLE_PATH, '..', 'library/')
    sources = yaml.load(open(OPENSHIFT_ANSIBLE_SOURCES_PATH).read())

    for fname, parts in sources.items():
        data = generate(parts)
        fname = os.path.join(library, fname)
        if args.verify:
            if not open(fname).read() == data.getvalue():
                raise GenerateAnsibleException('Generated content does not match for %s' % fname)

            continue

        with open(fname, 'w') as afd:
            afd.seek(0)
            afd.write(data.getvalue())


if __name__ == '__main__':
    main()
