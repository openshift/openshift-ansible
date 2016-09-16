[![Join the chat at https://gitter.im/openshift/openshift-ansible](https://badges.gitter.im/Join%20Chat.svg)](https://gitter.im/openshift/openshift-ansible)

#OpenShift Ansible

This repo contains Ansible code for OpenShift. This repo and the origin RPMs
that it installs currently require a package that provides `docker`. Currently
the RPMs provided from dockerproject.org do not provide this requirement, though
they may in the future.

##Branches
The master branch tracks our current work and should be compatible with both
Origin master branch and the current Origin stable release, currently that's
v1.3 and v1.2. Enterprise branches exist where we coordinate with internal Red
Hat Quality Assurance teams. Fixes and backwards compatible feature improvements
are often backported to the more current enterprise branches.  The enterprise
branches should also be compatible with the corresponding Origin release for
users who are looking for more conservative rate of change.


##Setup
- Install base dependencies:
  - Fedora:
  ```
    dnf install -y ansible-2.1.0.0 pyOpenSSL python-cryptography
  ```
   - OSX:
  ```
    # Install ansible 2.1.0.0 and python 2
    brew install ansible python
  ```
- Setup for a specific cloud:
  - [AWS](http://github.com/openshift/openshift-ansible/blob/master/README_AWS.md)
  - [GCE](http://github.com/openshift/openshift-ansible/blob/master/README_GCE.md)
  - [local VMs](http://github.com/openshift/openshift-ansible/blob/master/README_libvirt.md)

- Bring your own host deployments:
  - [OpenShift Enterprise](https://docs.openshift.com/enterprise/latest/install_config/install/advanced_install.html)
  - [OpenShift Origin](https://docs.openshift.org/latest/install_config/install/advanced_install.html)
  - [Atomic Enterprise](http://github.com/openshift/openshift-ansible/blob/master/README_AEP.md)

- Build
  - [How to build the openshift-ansible rpms](BUILD.md)

- Directory Structure:
  - [bin/cluster](https://github.com/openshift/openshift-ansible/tree/master/bin/cluster) - python script to easily create clusters
  - [docs](https://github.com/openshift/openshift-ansible/tree/master/docs) - Documentation for the project
  - [filter_plugins/](https://github.com/openshift/openshift-ansible/tree/master/filter_plugins) - custom filters used to manipulate data in Ansible
  - [inventory/](https://github.com/openshift/openshift-ansible/tree/master/inventory) - houses Ansible dynamic inventory scripts
  - [playbooks/](https://github.com/openshift/openshift-ansible/tree/master/playbooks) - houses host-type Ansible playbooks (launch, config, destroy, vars)
  - [roles/](https://github.com/openshift/openshift-ansible/tree/master/roles) - shareable Ansible tasks

##Contributing
- [Best Practices Guide](https://github.com/openshift/openshift-ansible/blob/master/docs/best_practices_guide.adoc)
- [Core Concepts](https://github.com/openshift/openshift-ansible/blob/master/docs/core_concepts_guide.adoc)
- [Style Guide](https://github.com/openshift/openshift-ansible/blob/master/docs/style_guide.adoc)
