# System container installer

These files are needed to run the installer using an [Atomic System container](http://www.projectatomic.io/blog/2016/09/intro-to-system-containers/).

* config.json.template - Template of the configuration file used for running containers.

* manifest.json - Used to define various settings for the system container, such as the default values to use for the installation. 

* run-system-container.sh - Entrypoint to the container.

* service.template - Template file for the systemd service.

* tmpfiles.template - Template file for systemd-tmpfiles.
