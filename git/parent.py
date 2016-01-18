#!/usr/bin/env python
'''
  Script to determine if this commit has also
  been merged through the stage branch
'''
#
#  Usage:
#    parent_check.py <branch> <commit_id>
#
#
import sys
import subprocess

def run_cli_cmd(cmd, in_stdout=None, in_stderr=None):
    '''Run a command and return its output'''
    if not in_stderr:
        proc = subprocess.Popen(cmd, bufsize=-1, stderr=subprocess.PIPE, stdout=subprocess.PIPE, shell=False)
    else:
        proc = subprocess.check_output(cmd, bufsize=-1, stdout=in_stdout, stderr=in_stderr, shell=False)
    stdout, stderr = proc.communicate()
    if proc.returncode != 0:
        return {"rc": proc.returncode, "error": stderr}
    else:
        return {"rc": proc.returncode, "result": stdout}

def main():
    '''Check to ensure that the commit that is currently
       being submitted is also in the stage branch.

       if it is, succeed
       else, fail
    '''
    branch = 'prod'

    if sys.argv[1] != branch:
        sys.exit(0)

    # git co stg
    results = run_cli_cmd(['/usr/bin/git', 'checkout', 'stg'])

    # git pull latest
    results = run_cli_cmd(['/usr/bin/git', 'pull'])

    # setup on the <prod> branch in git
    results = run_cli_cmd(['/usr/bin/git', 'checkout', 'prod'])

    results = run_cli_cmd(['/usr/bin/git', 'pull'])
    # merge the passed in commit into my current <branch>

    commit_id = sys.argv[2]
    results = run_cli_cmd(['/usr/bin/git', 'merge', commit_id])

    # get the differences from stg and <branch>
    results = run_cli_cmd(['/usr/bin/git', 'rev-list', '--left-right', 'stg...prod'])

    # exit here with error code if the result coming back is an error
    if results['rc'] != 0:
        print results['error']
        sys.exit(results['rc'])

    count = 0
    # Each 'result' is a commit
    # Walk through each commit and see if it is in stg
    for commit in results['result'].split('\n'):

        # continue if it is already in stg
        if not commit or commit.startswith('<'):
            continue

        # remove the first char '>'
        commit = commit[1:]

        # check if any remote branches contain $commit
        results = run_cli_cmd(['/usr/bin/git', 'branch', '-q', '-r', '--contains', commit], in_stderr=None)

        # if this comes back empty, nothing contains it, we can skip it as
        # we have probably created the merge commit here locally
        if results['rc'] == 0 and len(results['result']) == 0:
            continue

        # The results generally contain origin/pr/246/merge and origin/pr/246/head
        # this is the pull request which would contain the commit in question.
        #
        # If the results do not contain origin/stg then stage does not contain
        # the commit in question.  Therefore we need to alert!
        if 'origin/stg' not in results['result']:
            print "\nFAILED: (These commits are not in stage.)\n"
            print "\t%s" % commit
            count += 1

    # Exit with count of commits in #{branch} but not stg
    sys.exit(count)

if __name__ == '__main__':
    main()

