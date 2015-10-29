# oo-install Supported Configuration File

Upon completion oo-install will write out a configuration file representing the settings that were gathered and used. This configuration file, or one crafted by hand, can be used to run or re-run the installer and add additional hosts, upgrade, or re-install.

The default location this config file will be written to ~/.config/openshift/installer.cfg.yml.

## Example

```
variant: openshift-enterprise
variant_version: 3.0
ansible_ssh_user: root
hosts:
- ip: 10.0.0.1
  hostname: master-private.example.com
  public_ip: 24.222.0.1
  public_hostname: master.example.com
  master: true
  node: true
  containerized: true
- ip: 10.0.0.2
  hostname: node1-private.example.com
  public_ip: 24.222.0.2
  public_hostname: node1.example.com
  node: true
- ip: 10.0.0.3
  hostname: node2-private.example.com
  public_ip: 24.222.0.3
  public_hostname: node2.example.com
  node: true
```

## Primary Settings

### variant

The OpenShift variant to install. Currently valid options are:

 * openshift-enterprise
 * atomic-enterprise

### variant_version (optional)

Default: Latest version for your chosen variant.

A version which must be valid for your selected variant. If not specified the latest will be assumed.

Examples: 3.0, 3.1, etc.

### hosts

This section defines a list of the hosts you wish to install the OpenShift master/node service on.

*ip* or *hostname* must be specified so the installer can connect to the system to gather facts before proceeding with the install.

If *public_ip* or *public_hostname* are not specified, this information will be gathered from the facts and the user will be asked to confirm in an editor. For an unattended install, the installer will error out. (you must provide complete host records for an unattended install)

*master* and *node* determine the type of services that will be installed. One of these must be set to true for the configuration file to be considered valid.

*containerized* indicates you want to run OpenShift services in a container on this host.

### ansible_ssh_user

Default: root

Defines the user ansible will use to ssh to remote systems for gathering facts and the installation.

### ansible_log_path

Default: /tmp/ansible.log


