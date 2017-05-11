#!/usr/bin/python
# -*- coding: utf-8 -*-
# pylint: disable=missing-docstring,invalid-name

import random
import tempfile
import shutil
import os.path

# pylint: disable=redefined-builtin,wildcard-import,unused-wildcard-import
from ansible.module_utils.basic import *  # noqa: F403


DOCUMENTATION = '''
---
module: openshift_container_binary_sync
short_description: Copies OpenShift binaries out of the given image tag to host system.
'''


class BinarySyncError(Exception):
    def __init__(self, msg):
        super(BinarySyncError, self).__init__(msg)
        self.msg = msg


# pylint: disable=too-few-public-methods
class BinarySyncer(object):
    """
    Syncs the openshift, oc, oadm, and kubectl binaries/symlinks out of
    a container onto the host system.
    """

    def __init__(self, module, image, tag):
        self.module = module
        self.changed = False
        self.output = []
        self.bin_dir = '/usr/local/bin'
        self.image = image
        self.tag = tag
        self.temp_dir = None  # TBD

    def sync(self):
        container_name = "openshift-cli-%s" % random.randint(1, 100000)
        rc, stdout, stderr = self.module.run_command(['docker', 'create', '--name',
                                                      container_name, '%s:%s' % (self.image, self.tag)])
        if rc:
            raise BinarySyncError("Error creating temporary docker container. stdout=%s, stderr=%s" %
                                  (stdout, stderr))
        self.output.append(stdout)
        try:
            self.temp_dir = tempfile.mkdtemp()
            self.output.append("Using temp dir: %s" % self.temp_dir)

            rc, stdout, stderr = self.module.run_command(['docker', 'cp', "%s:/usr/bin/openshift" % container_name,
                                                          self.temp_dir])
            if rc:
                raise BinarySyncError("Error copying file from docker container: stdout=%s, stderr=%s" %
                                      (stdout, stderr))

            rc, stdout, stderr = self.module.run_command(['docker', 'cp', "%s:/usr/bin/oc" % container_name,
                                                          self.temp_dir])
            if rc:
                raise BinarySyncError("Error copying file from docker container: stdout=%s, stderr=%s" %
                                      (stdout, stderr))

            self._sync_binary('openshift')

            # In older versions, oc was a symlink to openshift:
            if os.path.islink(os.path.join(self.temp_dir, 'oc')):
                self._sync_symlink('oc', 'openshift')
            else:
                self._sync_binary('oc')

            # Ensure correct symlinks created:
            self._sync_symlink('kubectl', 'openshift')
            self._sync_symlink('oadm', 'openshift')
        finally:
            shutil.rmtree(self.temp_dir)
            self.module.run_command(['docker', 'rm', container_name])

    def _sync_symlink(self, binary_name, link_to):
        """ Ensure the given binary name exists and links to the expected binary. """

        # The symlink we are creating:
        link_path = os.path.join(self.bin_dir, binary_name)

        # The expected file we should be linking to:
        link_dest = os.path.join(self.bin_dir, link_to)

        if not os.path.exists(link_path) or \
                not os.path.islink(link_path) or \
                os.path.realpath(link_path) != os.path.realpath(link_dest):
            if os.path.exists(link_path):
                os.remove(link_path)
            os.symlink(link_to, os.path.join(self.bin_dir, binary_name))
            self.output.append("Symlinked %s to %s." % (link_path, link_dest))
            self.changed = True

    def _sync_binary(self, binary_name):
        src_path = os.path.join(self.temp_dir, binary_name)
        dest_path = os.path.join(self.bin_dir, binary_name)
        incoming_checksum = self.module.run_command(['sha256sum', src_path])[1]
        if not os.path.exists(dest_path) or self.module.run_command(['sha256sum', dest_path])[1] != incoming_checksum:
            shutil.move(src_path, dest_path)
            self.output.append("Moved %s to %s." % (src_path, dest_path))
            self.changed = True


def main():
    module = AnsibleModule(  # noqa: F405
        argument_spec=dict(
            image=dict(required=True),
            tag=dict(required=True),
        ),
        supports_check_mode=True
    )

    image = module.params['image']
    tag = module.params['tag']

    binary_syncer = BinarySyncer(module, image, tag)

    try:
        binary_syncer.sync()
    except BinarySyncError as ex:
        module.fail_json(msg=ex.msg)

    return module.exit_json(changed=binary_syncer.changed,
                            output=binary_syncer.output)


if __name__ == '__main__':
    main()
