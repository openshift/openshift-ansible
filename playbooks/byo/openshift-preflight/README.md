# OpenShift preflight checks

Here we provide an Ansible playbook for detecting potential roadblocks prior to
an install or upgrade.

Ansible's default operation mode is to fail fast, on the first error. However,
when performing checks, it is useful to gather as much information about
problems as possible in a single run.

The `check.yml` playbook runs a battery of checks against the inventory hosts
and tells Ansible to ignore intermediate errors, thus giving a more complete
diagnostic of the state of each host. Still, if any check failed, the playbook
run will be marked as having failed.

To facilitate understanding the problems that were encountered, we provide a
custom callback plugin to summarize execution errors at the end of a playbook
run.

---

*Note that currently the `check.yml` playbook is only useful for RPM-based
installations. Containerized installs are excluded from checks for now, but
might be included in the future if there is demand for that.*

---

## Running

With an installation of Ansible 2.2 or greater, run the playbook directly
against your inventory file. Here is the step-by-step:

1. If you haven't done it yet, clone this repository:

    ```console
    $ git clone https://github.com/openshift/openshift-ansible
    $ cd openshift-ansible
    ```

2. Run the playbook:

    ```console
    $ ansible-playbook -i <inventory file> playbooks/byo/openshift-preflight/check.yml
    ```
