# Consolidate plugins and shared defaults to lib_openshift

## Description
We have various plugins (modules, actions, filters) scattered throughout various
roles.  We should move all that code to one role, lib_openshift.

We have various defaults shared across many roles. We should put all openshift_x
shared variables in roles/lib_openshift/defaults/main.yml and back-reference
those variables in the roles that consume them.

We should use lib_openshift as the first meta-dependency for each role.

## Rationale
Better organization and easier reuse of custom modules and default variables.

## Design
Back-reference example:

```yaml
# roles/lib_openshift/defaults/main.yml
openshift_x: some-value
```

```yaml
# roles/openshift_role1/defaults/main.yml
openshift_role1_x: "{{ openshift_x }}"
```

## Checklist
* Move plugins to lib_openshift
* Include lib_openshift in all role meta dependencies.
* Migrate variables.

## User Story
As a developer on OpenShift-Ansible,
I want to not have to hunt for where modules are defined.
so that I can add new ones and modify existing ones.

As a developer on OpenShift-Ansible,
I want to have variables assigned default values, preferrably in one place, that
can be overridden by inventory variables.  It is not possible to use inventory
variables to override variables imported with include_vars or set with set_fact.

## Acceptance Criteria
* Contributors approve.
