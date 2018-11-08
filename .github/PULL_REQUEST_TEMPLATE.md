TEMPLATE
========
The pull request title should be one line summary that completes the sentence
"If merged, this change will ..."

PR Description should explain why the change is necessary and reasoning
behind the chosen implementation. If this is a backport please include a
link to the upstream PR. If this is related to a bugzilla please include a
link to the bugzilla.

Update the description throughout the life of the pull request so that it
is accurate at all times.


MASTER is 4.0
======
There is a branch for each major release, ex: release-3.11, release-3.10.
The master branch tracks the current development work. At this time that
is 4.x. Due to the scope of the changes involved in 4.0 it is likely that
any change targetting 3.x will not be relevant to the master branch.

PRs for 3.x releases should be opened directly against the latest release
that they are relevant to and then backported once accepted.



