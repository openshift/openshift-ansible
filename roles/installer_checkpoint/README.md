OpenShift-Ansible Installer Checkpoint
======================================

A complete OpenShift cluster installation is comprised of many different
components which can take 30 minutes to several hours to complete.  If the
installation should fail, it could be confusing to understand at which component
the failure occurred.  Additionally, it may be desired to re-run only the
component which failed instead of starting over from the beginning.  Components
which came after the failed component would also need to be run individually.

Design
------

The Installer Checkpoint implements an Ansible callback plugin to allow
displaying and logging of the installer status at the end of a playbook run.

To ensure the callback plugin is loaded, regardless of ansible.cfg file
configuration, the plugin has been placed inside the installer_checkpoint role
which must be called early in playbook execution. The `std_include.yml` playbook
is run first for all entry point playbooks, therefore, the initialization of the
checkpoint plugin has been placed at the beginning of that file.

Playbooks use the [set_stats][set_stats] Ansible module to set a custom stats
variable indicating the status of the phase being executed.

The installer_checkpoint.py callback plugin extends the Ansible
`v2_playbook_on_stats` method, which is called at the end of a playbook run, to
display the status of each phase which was run.  The INSTALLER STATUS report is
displayed immediately following the PLAY RECAP.

Phases of cluster installation are mapped to the steps in the
[common/openshift-cluster/config.yml][openshift_cluster_config] playbook.

To correctly display the order of the installer phases, the `installer_phases`
variable defines the phase or component order.

```python
        # Set the order of the installer phases
        installer_phases = [
            'installer_phase_initialize',
            'installer_phase_etcd',
            'installer_phase_nfs',
            'installer_phase_loadbalancer',
            'installer_phase_master',
            'installer_phase_master_additional',
            'installer_phase_node',
            'installer_phase_glusterfs',
            'installer_phase_hosted',
            'installer_phase_metrics',
            'installer_phase_logging',
            'installer_phase_servicecatalog',
        ]
```

Additional attributes, such as display title and component playbook, of each
phase are stored in the `phase_attributes` variable.

```python
        # Define the attributes of the installer phases
        phase_attributes = {
            'installer_phase_initialize': {
                'title': 'Initialization',
                'playbook': ''
            },
            'installer_phase_etcd': {
                'title': 'etcd Install',
                'playbook': 'playbooks/byo/openshift-etcd/config.yml'
            },
            'installer_phase_nfs': {
                'title': 'NFS Install',
                'playbook': 'playbooks/byo/openshift-nfs/config.yml'
            },
            #...
        }
```

Usage
-----

In order to indicate the beginning of a component installation, a play must be
added to the beginning of the main playbook for the component to set the phase
status to "In Progress".  Additionally, a play must be added after the last play
for that component to set the phase status to "Complete".  

The following example shows the first play of the 'installer phase' loading the
`installer_checkpoint` role, as well as the `set_stats` task for setting
`installer_phase_initialize` to "In Progress".  Various plays are run for the
phase/component and then a final play for setting `installer_hase_initialize` to
"Complete".

```yaml
# common/openshift-cluster/std_include.yml
---
- name: Initialization Checkpoint Start
  hosts: oo_all_hosts
  gather_facts: false
  roles:
  - installer_checkpoint
  tasks:
  - name: Set install initialization 'In Progress'
    set_stats:
      data:
        installer_phase_initialize: "In Progress"
      aggregate: false

#...
# Various plays here
#...

- name: Initialization Checkpoint End
  hosts: localhost
  connection: local
  gather_facts: false
  tasks:
  - name: Set install initialization 'Complete'
    set_stats:
      data:
        installer_phase_initialize: "Complete"
      aggregate: false
``` 

Each phase or component of the installer will follow a similar pattern, with the
exception that the `installer_checkpoint` role does not need to be called since
it was already loaded by the play in `std_include.yml`.  It is important to
place the 'In Progress' and 'Complete' plays as the first and last plays of the
phase or component.
 
Examples
--------

Example display of a successful playbook run:

```
PLAY RECAP *********************************************************************
master01.example.com : ok=158  changed=16   unreachable=0    failed=0
node01.example.com   : ok=469  changed=74   unreachable=0    failed=0
node02.example.com   : ok=157  changed=17   unreachable=0    failed=0
localhost            : ok=24   changed=0    unreachable=0    failed=0


INSTALLER STATUS ***************************************************************
Initialization             : Complete
etcd Install               : Complete
NFS Install                : Not Started
Load balancer Install      : Not Started
Master Install             : Complete
Master Additional Install  : Complete
Node Install               : Complete
GlusterFS Install          : Not Started
Hosted Install             : Complete
Metrics Install            : Not Started
Logging Install            : Not Started
Service Catalog Install    : Not Started
```

Example display if a failure occurs during execution:

```
INSTALLER STATUS ***************************************************************
Initialization             : Complete
etcd Install               : Complete
NFS Install                : Not Started
Load balancer Install      : Not Started
Master Install             : In Progress
     This phase can be restarted by running: playbooks/byo/openshift-master/config.yml
Master Additional Install  : Not Started
Node Install               : Not Started
GlusterFS Install          : Not Started
Hosted Install             : Not Started
Metrics Install            : Not Started
Logging Install            : Not Started
Service Catalog Install    : Not Started
```

[set_stats]: http://docs.ansible.com/ansible/latest/set_stats_module.html
[openshift_cluster_config]: https://github.com/openshift/openshift-ansible/blob/master/playbooks/common/openshift-cluster/config.yml
