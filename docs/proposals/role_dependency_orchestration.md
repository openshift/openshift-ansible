# Role dependency orchestration

## Towards loosely-coupled roles

Assume the following situation:
* role `<role>_common` defines variables that are common for various other roles
  that deal with upgrade, certificate deployment, migration, and other operations.
* each of corresponding `<role>_upgrade`, `<role>_migrate`, `<role>_certificates` roles depend
  on `<role>_common` role and consumes its role variables

Assume we have a play that upgrades a cluster component in the following sequence:

* re-deploy certificates by invoking `<role>_certificates` role
* upgrade component by invoking `<role>_upgrade` role
* migrate data of a component to new schema by invoking `<role>_migrate`

I.e.
```yaml
roles:
- role: <role>_certificates
- role: <role>_upgrade
- role: <role>_migrate
```

What are disadvantages of this approach:
* `<role>_common` role is invoked three times even if it needs to be invoked only once
  to set common variables.
* if the `<role>_upgrade` role needs only a small set of common variables,
  invoking `<role>_common` becomes an expensive operation.
* there may be various sources that produces proper values for `<role>_upgrade`
  role variables. It the `<role>_common` is invoked each time right before
  the upgrade role, it overrides all the common role variable no matter what they
  were set to before the invocation. Thus decreasing role modularity and re-usability.

## Role dependencies

A role can have two categories of dependencies:

* self-contained dependency: a dependency that has no role variable to set/read
* parametrized dependency: a dependency that has a set of input role variables

In the latter case there are two ways how to propagate role variables into role dependency:

* with a knowledge of role variables of role dependencies:

  ```yaml
  roles:
  - role: etcd
    r_etcd_client_port: 2379
    r_etcd_peer_port: 2380
    r_etcd_common_etcd_runtime: docker
    r_etcd_common_embedded_etcd: false
  ```

  Role variables of both roles (`etcd` and `etcd_common`) are set during `etcd`
  role invocation. Caller of the `etcd` role must be aware of all relevant
  `r_etcd_common` like variables of the `etcd_common` role.

* without a knowledge of role variables of role dependencies:

  ```yaml
  roles:
  - role: etcd
    r_etcd_peer_port: 2380
    r_etcd_etcd_runtime: docker
    r_etcd_embedded_etcd: false
  ```

  All `r_etcd_common_` like variables are duplicated and wired into their
  corresponding dependency variables in `etcd/meta/main.yml`:

  ```yaml
  dependencies:
  - role: etcd_common
    r_etcd_common_etcd_runtime: "{{ r_etcd_etcd_runtime }}"
    r_etcd_common_embedded_etcd: "{{ r_etcd_embedded_etcd }}"
  ```

Both ways have its advantages and disadvantages. In either way, the `etcd` role
depends on the `etcd_common` role.

Aim of the proposal is to eliminate role dependencies wherever it is possible
in favor of applying the following approach:

```yaml
- include_role:
    name: etcd_common
  vars:
    r_etcd_common_etcd_runtime: docker
    r_etcd_common_embedded_etcd: false

- include_role:
    name: etcd
  vars:
    r_etcd_peer_port: 2380
    r_etcd_etcd_runtime: docker
    r_etcd_runtime: "{{ r_etcd_common_etcd_runtime }}"
    r_etcd_service: "{{ r_etcd_common_service }}"
    r_etcd_service_file: "{{ r_etcd_common_service_file }}"
```

Which resuls in:

* `etcd_common` dependency of `etcd` role is removed
* all `r_etcd_common_` like variables needed in the `etcd` role are wired
  through `r_etcd_` like variables
* both role are handled as functions with a set of parameters and return values
* each role deals with its own set of role variables, one is independent of the other

In general, if a role A depends on role B both roles are orchestrated via
the following pattern:

```yaml
- include_role:
    name: A
  vars:
    r_A_<var>: <value>
    r_A_<var>: <value>
    ...

- include_role:
    name: B
  vars:
    r_B_<var>: <value>
    r_B_<var>: <value>
    ...
    r_B_<var>: "{{ r_A_<var> }}"
    r_B_<var>: "{{ r_A_<var> }}"
    ...
```

All A role variables the B role needs are propagated through B role variables.

## Proposal

Orchestrate roles and its dependencies in the following manner:
* a role is forbidden to consume any role variable of its dependency
* a role is forbidden to set any role variable of its dependency
* all relevant role variables are set right before a role is invoked
* if role B needs role variables from role A, role A is invoked before role B
  and the required A role variables are set to role B variables during role B invocation

## Example

The `etcd_upgrade` role depends on `etcd_common` role. Once the principles from
the proposal are applied, the invocation chain corresponds to:

```yaml
- name: A play
  tasks:
  - include_role:
      name: etcd_common
    vars:
      r_etcd_common_etcd_runtime: "{{ openshift.common.etcd_runtime }}"

  - include_role:
      name: etcd_upgrade
    vars:
      r_etcd_upgrade_action: upgrade
      r_etcd_upgrade_mechanism: rpm
      r_etcd_upgrade_version: "3.1.9"
      r_etcd_upgrade_etcd_runtime: "{{ openshift.common.etcd_runtime }}"
      r_etcd_upgrade_service: "{{ r_etcd_common_service }}"
      r_etcd_upgrade_service_file: "{{ r_etcd_common_service_file }}"
      r_etcd_upgrade_etcdctlv2: "{{ r_etcd_common_etcdctlv2 }}"
```

The `etcd_common` is producing `r_etcd_common_etcdctlv2`, `r_etcd_common_service_file`
and `r_etcd_common_service` which are wired to the `etcd_upgrade` through its role
variables. At the same time the `etcd_common` dependency is removed from the upgrade
role.
