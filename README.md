#OpenShift and Atomic Enterprise Ansible

This repo contains Ansible code for OpenShift and Atomic Enterprise.

##Setup
- Install base dependencies:
  - Fedora:
  ```
    dnf install -y ansible-1.9.4 rubygem-thor rubygem-parseconfig util-linux pyOpenSSL libffi-devel python-cryptography
  ```
   - OSX:
  ```
    # Install ansible 1.9.4 and python 2
    brew install ansible python
    # Required ruby gems
    gem install thor parseconfig
  ```
- Setup for a specific cloud:
  - [AWS](README_AWS.md)
  - [GCE](README_GCE.md)
  - [local VMs](README_libvirt.md)

- Bring your own host deployments:
  - [OpenShift Enterprise](README_OSE.md)
  - [OpenShift Origin](README_origin.md)
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

###Feature Roadmap
Our Feature Roadmap is available on the OpenShift Origin Infrastructure [Trello board](https://trello.com/b/nbkIrqKa/openshift-origin-infrastructure). All ansible items will be tagged with [installv3].
