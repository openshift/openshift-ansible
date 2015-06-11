#openshift-ansible

This repo contains OpenShift Ansible code.

##Setup
- Install base dependencies:
  - Fedora:
  ```
    yum install -y ansible rubygem-thor rubygem-parseconfig util-linux
  ```
   - OSX:
  ```
    # Install ansible and python 2
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

- Build
  - [How to build the openshift-ansible rpms](BUILD.md)

- Directory Structure:
  - [bin/cluster](bin/cluster) - python script to easily create OpenShift 3 clusters
  - [docs](docs) - Documentation for the project
  - [filter_plugins/](filter_plugins) - custom filters used to manipulate data in Ansible
  - [inventory/](inventory) - houses Ansible dynamic inventory scripts
  - [playbooks/](playbooks) - houses host-type Ansible playbooks (launch, config, destroy, vars)
  - [roles/](roles) - shareable Ansible tasks

##Contributing

###Feature Roadmap
Our Feature Roadmap is available on the OpenShift Origin Infrastructure [Trello board](https://trello.com/b/nbkIrqKa/openshift-origin-infrastructure). All ansible items will be tagged with [installv3].
