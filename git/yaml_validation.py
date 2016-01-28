#!/usr/bin/env python
#
#  python yaml validator for a git commit
#
'''
python yaml validator for a git commit
'''
import shutil
import sys
import os
import tempfile
import subprocess
import yaml

def get_changes(oldrev, newrev, tempdir):
    '''Get a list of git changes from oldrev to newrev'''
    proc = subprocess.Popen(['/usr/bin/git', 'diff', '--name-only', oldrev,
                             newrev, '--diff-filter=ACM'], stdout=subprocess.PIPE)
    stdout, _ = proc.communicate()
    files = stdout.split('\n')

    # No file changes
    if not files:
        return []

    cmd = '/usr/bin/git archive %s %s | /bin/tar x -C %s' % (newrev, " ".join(files), tempdir)
    proc = subprocess.Popen(cmd, shell=True)
    _, _ = proc.communicate()

    rfiles = []
    for dirpath, _, fnames in os.walk(tempdir):
        for fname in fnames:
            rfiles.append(os.path.join(dirpath, fname))

    return rfiles

def main():
    '''
    Perform yaml validation
    '''
    results = []
    try:
        tmpdir = tempfile.mkdtemp(prefix='jenkins-git-')
        old, new, _ = sys.argv[1:]

        for file_mod in get_changes(old, new, tmpdir):

            print "+++++++ Received: %s" % file_mod

            # if the file extensions is not yml or yaml, move along.
            if not file_mod.endswith('.yml') and not file_mod.endswith('.yaml'):
                continue

            # We use symlinks in our repositories, ignore them.
            if os.path.islink(file_mod):
                continue

            try:
                yaml.load(open(file_mod))
                results.append(True)

            except yaml.scanner.ScannerError as yerr:
                print yerr
                results.append(False)
    finally:
        shutil.rmtree(tmpdir)

    if not all(results):
        sys.exit(1)

if __name__ == "__main__":
    main()

