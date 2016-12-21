# Running Tests (NEW)

Run the command:

    make ci

to run an array of unittests locally.

Underneath the covers, we use [tox](http://readthedocs.org/docs/tox/) to manage virtualenvs and run
tests. Alternatively, tests can be run using [detox](https://pypi.python.org/pypi/detox/) which allows
for running tests in parallel


```
pip install tox detox
```

List the test environments available:
```
tox -l
```

Run all of the tests with:
```
tox
```

Run all of the tests in parallel with detox:
```
detox
```

Running a particular test environment (python 2.7 flake8 tests in this case):
```
tox -e py27-ansible22-flake8
```

Running a particular test environment in a clean virtualenv (python 3.5 pylint
tests in this case):
```
tox -r -e py35-ansible22-pylint
```

If you want to enter the virtualenv created by tox to do additional
testing/debugging (py27-flake8 env in this case):
```
source .tox/py27-ansible22-flake8/bin/activate
```

You will get errors if the log files already exist and can not be
written to by the current user (`/tmp/ansible.log` and
`/tmp/installer.txt`). *We're working on it.*

# Running From Source

You will need to setup a **virtualenv** to run from source:

    $ virtualenv oo-install
    $ source ./oo-install/bin/activate
    $ virtualenv --relocatable ./oo-install/
    $ python setup.py install

The virtualenv `bin` directory should now be at the start of your
`$PATH`, and `oo-install` is ready to use from your shell.

You can exit the virtualenv with:

    $ deactivate

# Testing (OLD)

*This section is deprecated, but still works*

First, run the **virtualenv setup steps** described above.

Install some testing libraries: (we cannot do this via setuptools due to the version virtualenv bundles)

$ pip install mock nose

Then run the tests with:

$ oo-install/bin/nosetests
