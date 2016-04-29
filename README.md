[![Join the chat at https://gitter.im/openshift/openshift-ansible](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/openshift/openshift-ansible)

#OpenShift Ansible

This repo contains Ansible code for OpenShift

##Setup
- Install base dependencies:
  - Fedora:
  ```
    dnf install -y ansible-1.9.4 pyOpenSSL python-cryptography
  ```
   - OSX:
  ```
    # Install ansible 1.9.4 and python 2
    brew install ansible python
  ```
- Setup for a specific cloud:
  - [AWS](README_AWS.md)
  - [GCE](README_GCE.md)
  - [local VMs](README_libvirt.md)

- Bring your own host deployments:
  - [OpenShift Enterprise](https://docs.openshift.com/enterprise/latest/install_config/install/advanced_install.html)
  - [OpenShift Origin](https://docs.openshift.org/latest/install_config/install/advanced_install.html)
  - [Atomic Enterprise](README_AEP.md)

- Build
  - [How to build the openshift-ansible rpms](BUILD.md)

- Directory Structure:
  - [bin/cluster](bin/cluster) - python script to easily create clusters
  - [docs](docs) - Documentation for the project
  - [filter_plugins/](filter_plugins) - custom filters used to manipulate data in Ansible
  - [inventory/](inventory) - houses Ansible dynamic inventory scripts
  - [playbooks/](playbooks) - houses host-type Ansible playbooks (launch, config, destroy, vars)
  - [roles/](roles) - shareable Ansible tasks

##Contributing
- [Best Practices Guide](docs/best_practices_guide.adoc)
- [Core Concepts](docs/core_concepts_guide.adoc)
- [Style Guide](docs/style_guide.adoc)
