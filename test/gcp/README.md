# OpenShift 4.0 on GCP - Not Supported
This is for internal development purposes only and is not supported by Red Hat. Don't use this.

# Initial Setup 

## Requirements

[OpenShift Installer](https://github.com/openshift/installer)

[Ansible 2.7](https://docs.ansible.com/ansible/2.5/installation_guide/intro_installation.html) 
```
pip install -U apache-libcloud~=2.2.1
pip install google-auth
yum install -y google-cloud-sdk python2-crypto
```
## Credentials
Place the following files in the root of OpenShift-Ansible with the given filename:

* GCP service account key: `gce.json`
* OpenShift pull secret: `try.openshift.com.json`

## files_dir
Point to the above credentials and any assets you will generate:
```
# Execute this from the root dir
echo files_dir: $PWD > inventory/dynamic/gcp/group_vars/all/00_default_files_dir.yml
```

## Prepare Inventory Variables
You can use the example files for GCP:
```
cp test/gcp/examples/group_vars/* inventory/dynamic/gcp/group_vars/all/
```
You will also need to change the `remote_user` value in `inventory/dynamic/gcp/ansible.cfg` from `cloud-user` to your GCP username.


# Environment Variables
During each session, make sure you have the following environment variables and are authenticated to GCP:
```
export ANSIBLE_CONFIG="inventory/dynamic/gcp/ansible.cfg"
export INSTANCE_PREFIX=$(whoami)
```

```
gcloud auth activate-service-account --quiet --key-file="gce.json"
```
You can confirm login with: `gcloud compute --project "openshift-gce-devel" instances list`.


# Install Steps
Now you are ready to start the installation process. All of these commands should be executed from the root directory of OpenShift-Ansible.


To be safe, first remove any assets that may have been generated in a previous run. Then generate the install-config as an intermediate step
to generating the ignition configs, after which you will be ready to run the playbooks.
```
rm .openshift_install_state.json *.ign
./test/gcp/create-install-config.sh 
openshift-install create ignition-configs
ansible-playbook -vvv test/gcp/launch.yml
```
Keep in mind that the certs contained in the ignition-configs are valid for 30 minutes.
