# Running Tests

Run the command:

    make ci

to run tests and linting tools.

Underneath the covers, we use [tox](http://readthedocs.org/docs/tox/) to manage virtualenvs and run
tests. Alternatively, tests can be run using [detox](https://pypi.python.org/pypi/detox/) which allows
for running tests in parallel.

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

Run a particular test environment:

```
tox -e py27-flake8
```

Run a particular test environment in a clean virtualenv:

```
tox -r -e py35-pylint
```

If you want to enter the virtualenv created by tox to do additional
testing/debugging:

```
source .tox/py27-flake8/bin/activate
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
