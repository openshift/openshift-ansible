## Running From Source

You will need to setup a virtualenv to run from source and execute the unit tests.

$ virtualenv oo-install
$ source ./oo-install/bin/activate
$ virtualenv --relocatable ./oo-install/
$ python setup.py install

The virtualenv bin directory should now be at the start of your $PATH, and oo-install is ready to use from your shell.

You can exit the virtualenv with:

$ deactivate

## Testing

Install some testing libraries: (we cannot do this via setuptools due to the version virtualenv bundles)

$ pip install mock nose

Then run the tests with:

$ oo-install/bin/nosetests
