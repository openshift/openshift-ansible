# Do Not Use

Anything contained in this directory is unsupported and should not be used
to provision any OpenShift clusters.  Please refer to official documentation
for supported installation methods.

## How to use
Don't use it.

clone https://github.com/openshift/aos-ansible/pull/74 to ~/git/aos-ansible
(Red Hat use only)

Ensure openshift-install and terraform are in your path.

cd to this directory.

source installrc; export variables you want to override.  You'll need to at least
update what image you want to use unless you have that exact image in that exact
place.

./deploy.sh
This will generate install assets (inventory, install-config.yml, tfvars),
provision instances via terraform and start installation of
openshift-ansible.

Afterwards, you can cleanup with ./cleanup.sh
