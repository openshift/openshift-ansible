This directory contains scripts and other files that are executed by our
CI integration tests.

CI should call a script.  The only arguments that each script should accept
are:

1) Path to openshift-ansible/playbooks
2) Inventory path.
3) Extra vars path.

Ideally, inventory path and extra vars should live somewhere in this
subdirectory instead of the CI's source.

Extravars should typically be unnecessary.
