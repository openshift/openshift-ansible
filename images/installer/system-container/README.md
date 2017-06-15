# System container installer

These files are needed to run the installer using an [Atomic System container](http://www.projectatomic.io/blog/2016/09/intro-to-system-containers/).

* config.json.template - Template of the configuration file used for running containers.

* manifest.json - Used to define various settings for the system container, such as the default values to use for the installation. 

* run-system-container.sh - Entrypoint to the container.

* service.template - Template file for the systemd service.

* tmpfiles.template - Template file for systemd-tmpfiles.

## Options

These options may be set via the ``atomic`` ``--set`` flag. For defaults see ``root/exports/manifest.json``

* OPTS - Additional options to pass to ansible when running the installer

* VAR_LIB_OPENSHIFT_INSTALLER - Full path of the installer code to mount into the container

* VAR_LOG_OPENSHIFT_LOG - Full path of the log file to mount into the container

* PLAYBOOK_FILE - Full path of the playbook inside the container

* HOME_ROOT - Full path on host to mount as the root home directory inside the container (for .ssh/, etc..)

* ANSIBLE_CONFIG - Full path for the ansible configuration file to use inside the container

* INVENTORY_FILE - Full path for the inventory to use from the host
