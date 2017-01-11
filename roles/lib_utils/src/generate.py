#!/usr/bin/env python
'''
  Generate the openshift-ansible/roles/lib_openshift_cli/library/ modules.
'''

import os
import yaml

# pylint: disable=anomalous-backslash-in-string
GEN_STR = "#!/usr/bin/env python\n" + \
          "# pylint: disable=missing-docstring\n" + \
          "#     ___ ___ _  _ ___ ___    _ _____ ___ ___\n" + \
          "#    / __| __| \| | __| _ \  /_\_   _| __|   \\\n" + \
          "#   | (_ | _|| .` | _||   / / _ \| | | _|| |) |\n" + \
          "#    \___|___|_|\_|___|_|_\/_/_\_\_|_|___|___/_ _____\n" + \
          "#   |   \ / _ \  | \| |/ _ \_   _| | __|   \_ _|_   _|\n" + \
          "#   | |) | (_) | | .` | (_) || |   | _|| |) | |  | |\n" + \
          "#   |___/ \___/  |_|\_|\___/ |_|   |___|___/___| |_|\n"

OPENSHIFT_ANSIBLE_PATH = os.path.dirname(os.path.realpath(__file__))
OPENSHIFT_ANSIBLE_SOURCES_PATH = os.path.join(OPENSHIFT_ANSIBLE_PATH, 'generate_sources.yml')  # noqa: E501


def main():
    ''' combine the necessary files to create the ansible module '''

    library = os.path.join(OPENSHIFT_ANSIBLE_PATH, '..', 'library/')
    sources = yaml.load(open(OPENSHIFT_ANSIBLE_SOURCES_PATH).read())
    for fname, parts in sources.items():
        with open(os.path.join(library, fname), 'w') as afd:
            afd.seek(0)
            afd.write(GEN_STR)
            for fpart in parts:
                with open(os.path.join(OPENSHIFT_ANSIBLE_PATH, fpart)) as pfd:
                    # first line is pylint disable so skip it
                    for idx, line in enumerate(pfd):
                        if idx in [0, 1] and 'flake8: noqa' in line \
                           or 'pylint: skip-file' in line:
                            continue

                        afd.write(line)


if __name__ == '__main__':
    main()
