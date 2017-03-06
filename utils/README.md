# Running Tests

All tests can be run by running `tox`. See [running tests](..//CONTRIBUTING.md#running-tests) for more information.

# Running From Source

You will need to setup a **virtualenv** to run from source:

    $ virtualenv oo-install
    $ source oo-install/bin/activate
    $ python setup.py develop

The virtualenv `bin` directory should now be at the start of your
`$PATH`, and `oo-install` is ready to use from your shell.

You can exit the virtualenv with:

    $ deactivate
