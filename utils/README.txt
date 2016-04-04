## Running From Source

You will need to install tito and use it to build an rpm from source.
tito is available by default in Fedora and through EPEL for RHEL or CENTOS.

$ yum install tito
$ echo "NO_AUTO_INSTALL=openshift-ansible-zabbix" >> ~/.titorc
$ tito build --test --rpm --install

You can now run the quick installer with:

$ atomic-openshift-installer

## Testing

Install some testing libraries: (we cannot do this via setuptools due to the version virtualenv bundles)

$ pip install mock nose

Then run the tests with:

$ oo-install/bin/nosetests
