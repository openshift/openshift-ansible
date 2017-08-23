# Action based roles

## Avoid duplication, hide decision in implementation details.

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

## Proposal

In case a set of roles conforms to the following conditions:

* each role is responsible for a distinct operation (e.g. installation, upgrade, migration)
* all operations are applied on the same component
* the operations share common code base and Ansible resources

consolidate all roles into new one, providing a mechanism to select specific
operation to apply when the new role is invoked. Once can either go with

* variable-based operation selection:
  ```yaml
  include_role:
    name: <role>
  vars:
    r_<role>_action: <operation>
  ```

* or with file-based operation selection:
```yaml
include_role:
  name: <role>
tasks_from: <operation>.yml
```

Additionally, one can define a minimal set of actions that each action-based
role should provide:
* pre-checks: to check if the role has all necessary conditions fulfilled
* post-checks: to check a role ended successfully

### Layout

Proposed layout an action-based role (with variable-based operation selection):

**default/main.yml**
```yaml
...
# description="action selector" choices=["install", "upgrade", "migrate", "backup"]
r_<role>_action: install
...
```

**tasks/main.yml**:

```yaml
...
# run some checks
- name: Fail if invalid r_<role>_action provided
  fail:
    msg: "<role> role can only be called with 'install', 'upgrade', 'migrate' or 'backup'"
  when: r_<role>_action not in ['install', 'upgrade', 'migrate' or 'backup']
...
- name: Include main action task file
  include: "{{ r_<role>_action }}.yml"
...
```

Each action then correspond to a single file under **tasks** directory:

* `tasks/install.yml`
* `tasks/upgrade.yml`
* `tasks/migrate.yml`
* `tasks/backup.yml`

In case the operation selection is file-based, the `tasks/main.yml` is removed
and all relevant pre-checks included in all the action tasks files.

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
