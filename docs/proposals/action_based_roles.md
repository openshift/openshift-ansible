# Action based roles

## Description

Some of the openshift-ansible roles share common resources and spread responsibility
for a single action (or operation) among multiple roles. That leads to a code duplication,
degradation of code usability, increase of maintenance efforts, etc.

All such roles should be consolidated into a single role providing a mechanism
to invoke a particular piece of a code.

From here on, an action stands for implementation of an operation.

## Rationale

Each component lives through defined life-cycle phases. At the beginning
a component is installed. As time passes new version of the component is
available resulting in component upgrade. Under certain conditions one needs
to carry additional operations to update successfully such as migration,
backup or post-verification.

Given each of the operations are applied on the same component, some of the operation
underlying tasks, variables and other Ansible resources are shared. E.g. templates
of service files, handlers, sequence of installation or configuration tasks.

Additionally, some operations can be unified into one and the proper behavior hidden
inside a role as implementation details. E.g. component upgrade can be equivalent
to component installation up to some differences. The role dealing with the installation
should then decide if the actual installation or rather an update is required.

In practice, it is natural to create a role that deals with an installation as
the first step. Later, role that deals with an upgrade is implemented. Not rarely
followed by implementation of other operations. At the end one can end up
with a set of roles, each responsible for a single operation. Naturally,
the layout leads to code duplication and various efforts to minimize it.

## Design
In case a set of roles conforms to the following conditions:

* each role is responsible for a distinct operation (e.g. installation, upgrade, migration)
* all operations are applied on the same component
* the operations share common code base and Ansible resources

consolidate all roles into new one, providing a mechanism to select specific
operation to apply when the new role is invoked. Since Ansible 2.2 one can
use `include_role` module and perform file-based operation selection:

```yaml
include_role:
  name: <role>
tasks_from: <operation>
```

Additionally, one can define a minimal set of actions that each action-based
role should provide:
* pre-checks: to check if the role has all necessary conditions fulfilled
* post-checks: to check a role ended successfully

### Layout

Proposed layout of an action-based role:

```sh
$ ls <role>/tasks
<action1_dir>
<action2_dir>
...
<action1>.yml
<action2>.yml
...
```

The role `tasks` directory consists of:
* one directory per each action (action directory)
* one yml file per each action (action entry-point)
* additional yml files needed by the role (e.g. task files shared across actions)

Templates and other resources location are not affected by the layout.
If reasonable, the action directory layout can be duplicated inside the `templates` directory.

**Expected content of an action file**:

```yaml
# content of tasks/<action>.yml

# tasks common for actions, e.g. pre-checks, initialization
- name: Include <common> tasks
  include: <common>.yml
...
- <tasks>:
    <task_param>: "{{ <value> }}"
    ...
...
# sub-actions finishing implementation of the action
- include: <action>/<subaction1>.yml
- include: <action>/<subaction2>.yml
```

The pattern in the action file allows to:
- further decompose the action into sub-actions (increase re-usability)
- compose implementation of an action in the role tasks directory from common tasks and sub-actions
- easy-to-understand tasks flow (a single entry-point for each action in the role tasks directory, no entry-point in the action directory)

If an action directory was created from a previously existing role,
it contains all the role's tasks files.
If it was created as a new action, it contains all tasks files needed
to implement the action.

### Usage

```yaml
- hosts: <hosts>
  tasks:
  ...
  - include_role:
      name: <role>
      tasks_from: <action>
    vars:
      <var1>: "{{ <value1> }}"
      <var2>: "{{ <value2> }}"
      ...
```

If the `tasks/main.yml` is present, `include_role` without the `tasks_from`
can correspond to invocation of a default action.
The `tasks/main.yml` can provide additional comments about expected usage:

```yaml
# This role is intended to be used with include_role. E.g.
# include_role:
#   name:  <role>
#   tasks_from: "{{ item }}"
# with_items:
#   - pre_checks
#   - install
#   - verify
```

### Application of action-based roles

#### Stratification

A set of non-overlapping role actions can correspond to a set of well-defined phases.
One can decide to first run the same phase across all roles and wait for completion
before moving to run all the roles in a different phase. The phases can be broken out
into the following categories:

* **Informational** - determine values and set facts accordingly (either as local/private
  variables or role variable outputs). In some plays (e.g. for checks) this might
  be the only phase to run.
* **Pre-validation** - determine whether a role has all it needs to run,
  for example RPMs / images / tools on localhost, and whether the variables
  provided actually make sense (are defined, well-formed, consistent, come from
  an acceptable set, etc.) for the purpose of failing fast before any roles make any changes.
* **Run** - make changes that the role is intended for
* **Post-validation** - check whether the actions the role took actually worked;
  for instance, if the role defines a router, check that the routing pod(s) are actually
  running, so that we don't declare success and leave the user to figure out nothing
  is actually running. This phase could run repeatedly until success, defined failure,
  or timeout.

## Checklist
* [ ] make a list of candidate roles for consolidation (one for each sensible component)
* [ ] find occurrence of every consolidated roles and make sure it can be replaced by new role
* [ ] consolidate roles and update affected plays and roles
* [ ] document each new role

## User Story
As a developer on OpenShift-Ansible,
I want to consolidate all roles into a single one
so that I can
* eliminate duplication of resources
* attract a code of the same semantics into one place to increase modularity
* provide a well defined list of actions/operations a role can perform
* decrease the number of openshift-ansible roles to maintain

## Acceptance Criteria
* Verify that each new role provides at least the same functionality as all its underlying consolidated roles
* Verify that each replacement of a role inside a play (and/or a role dependency) provides the same functionality
* Verify that each new role is well documented

## References
* [Known issue] include_role does not expose variables to rest of playbook: https://github.com/ansible/ansible/issues/21890
