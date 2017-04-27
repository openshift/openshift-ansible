# OpenShift health checks

This directory contains Ansible playbooks for detecting potential problems prior
to an install, as well as health checks to run on existing OpenShift clusters.

Ansible's default operation mode is to fail fast, on the first error. However,
when performing checks, it is useful to gather as much information about
problems as possible in a single run.

Thus, the playbooks run a battery of checks against the inventory hosts and have
Ansible gather intermediate errors, giving a more complete diagnostic of the
state of each host. If any check failed, the playbook run will be marked as
failed.

To facilitate understanding the problems that were encountered, a custom
callback plugin summarizes execution errors at the end of a playbook run.

# Available playbooks

1. Pre-install playbook ([pre-install.yml](pre-install.yml)) - verifies system
   requirements and look for common problems that can prevent a successful
   installation of a production cluster.

2. Diagnostic playbook ([health.yml](health.yml)) - check an existing cluster
   for known signs of problems.

3. Certificate expiry playbooks ([certificate_expiry](certificate_expiry)) -
   check that certificates in use are valid and not expiring soon.

## Running

With a [recent installation of Ansible](../../../README.md#setup), run the playbook
against your inventory file. Here is the step-by-step:

1. If you haven't done it yet, clone this repository:

    ```console
    $ git clone https://github.com/openshift/openshift-ansible
    $ cd openshift-ansible
    ```

2. Run the appropriate playbook:

    ```console
    $ ansible-playbook -i <inventory file> playbooks/byo/openshift-checks/pre-install.yml
    ```

    or

    ```console
    $ ansible-playbook -i <inventory file> playbooks/byo/openshift-checks/health.yml
    ```

    or

    ```console
    $ ansible-playbook -i <inventory file> playbooks/byo/openshift-checks/certificate_expiry/default.yaml -v
    ```

## Running via Docker image

This repository is built into a Docker image including Ansible so that it can
be run anywhere Docker is available. Instructions for doing so may be found
[in the README](../../README_CONTAINER_IMAGE.md).

