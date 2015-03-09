openshift-ansible
========================

This repo contains OpenShift Ansible code.

Setup
-----
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

- Directory Structure:
  - [cloud.rb](cloud.rb) - light wrapper around Ansible
  - [cluster.sh](cluster.sh) - easily create OpenShift 3 clusters
  - [filter_plugins/](filter_plugins) - custom filters used to manipulate data in Ansible
  - [inventory/](inventory) - houses Ansible dynamic inventory scripts
  - [lib/](lib) - library components of cloud.rb
  - [playbooks/](playbooks) - houses host-type Ansible playbooks (launch, config, destroy, vars)
  - [roles/](roles) - shareable Ansible tasks
