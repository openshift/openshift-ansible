"""A setuptools based setup module.

"""

# Always prefer setuptools over distutils
from setuptools import setup

setup(
    name='ooinstall',

    # Versions should comply with PEP440.  For a discussion on single-sourcing
    # the version across setup.py and the project code, see
    # https://packaging.python.org/en/latest/single_source_version.html
    version="3.0.0",

    description="Ansible wrapper for OpenShift Enterprise 3 installation.",

    # The project's main homepage.
    url="https://github.com/openshift/openshift-ansible",

    # Author details
    author="openshift@redhat.com",
    author_email="OpenShift",

    # Choose your license
    license="Apache 2.0",

    # See https://pypi.python.org/pypi?%3Aaction=list_classifiers
    classifiers=[
        'Development Status :: 4 - Beta',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 2.7',
        'Topic :: Utilities',
    ],

    # What does your project relate to?
    keywords='oo-install setuptools development',

    # You can just specify the packages manually here if your project is
    # simple. Or you can use find_packages().
    packages=['ooinstall'],
    package_dir={'': 'src'},

    # List run-time dependencies here.  These will be installed by pip when
    # your project is installed. For an analysis of "install_requires" vs pip's
    # requirements files see:
    # https://packaging.python.org/en/latest/requirements.html
    install_requires=['click', 'PyYAML', 'ansible'],

    # If there are data files included in your packages that need to be
    # installed, specify them here.  If using Python 2.6 or less, then these
    # have to be included in MANIFEST.in as well.
    package_data={
        'ooinstall': ['ansible.cfg', 'ansible-quiet.cfg', 'ansible_plugins/*'],
    },

    # To provide executable scripts, use entry points in preference to the
    # "scripts" keyword. Entry points provide cross-platform support and allow
    # pip to create the appropriate form of executable for the target platform.
    entry_points={
        'console_scripts': [
            'oo-install=ooinstall.cli_installer:cli',
        ],
    },
)
