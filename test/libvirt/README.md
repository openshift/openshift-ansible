# Do Not Use

Anything contained in this directory is unsupported and should not be used
to provision any OpenShift clusters.  Please refer to official documentation
for supported installation methods.

## How to use
Don't use it.

cd to this directory.
source installrc; export variables you want to override.
./deploy.sh
This will generate install assets (inventory, install-config.yml, tfvars),
provision instances via terraform and start installation of
openshift-ansible.
