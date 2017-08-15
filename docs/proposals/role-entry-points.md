# Entry-point based roles

## We have a problem

Each role consists of a set of tasks and variables read/set in some of the tasks.
Some of the tasks can store their results into registered variables,
e.g. store stdout of a docker pull command.
Some of the tasks may be run only under certain condition that are generated
outside of a role, e.g. pull images only if a deployment is containerized.
Some of the tasks are run only if a certain variable is defined,
e.g. add additional Kubelet arguments into the `node-config.yml`
if `kubelet_additional_args` inventory variable is defined.

Some roles work with a lot of variables that from a point of a role are uninvited citizens.
Some of the variables are set inside a role, some of them are set outside of a role.
The variables outside of a role are hard to track, hard to determine their value or
a condition under which the variables are defined. These unknown facts make a role harder
to maintain, harder to make a role closed with respect to variables and to make
a role practically modular.

## Proposal

Make a role that conforms to the following conditions:
* none of the variables read/set inside a role are global
* all variables inside a role are `r_` (`r` standing for a role) and/or `l_`(`l` standing for a local) prefixed
* all values are propagated to a role through `r_` prefixed variables only
* all values that are set inside a role are read outside of a role through `r_` prefixed variables only
* all available `r_` prefixed variables are documented and checked before a main role task is run
* a table of `r_` prefixed variables in README.md is automatically generated

### Terminilogy

**Role variables**: All `r_` prefixed variables read/set inside a role

**Local variables**: All `l_` prefixed variables set inside a role

### Role properties

**Solid API**: all variables that a role caller can set need to be well defined.
It means each such variable must have the following information attached:
* name
* description
* default value (if the variable is defined)
* set of acceptable values
* if it is required or if it is optional

Well defined API allows automatically generated documentation and variable checks.

**Free of outer variables**: only variables consisting the role API or defined locally are allowed.
Any other variable (e.g. inventory variable or a variable set in a play) are forbidden.
A role free of any outer variable:
* can be shared across different Ansible solutions (improves modularity)
* is easier to test as only the role variables need to be set (improves role based testing)
* independent of variable name changes outside of a role (improves role independence)

### Role variables

#### Where the role variables live (with annotations?)

All role variables live under `default/main.yml` file.
The file is to be structured in the following way:
```yaml
# List of required undefined variables:
#: name=r_openshift_node_deployment_type, required=true, description="Deployment type", choices=['origin', 'openshift-enterprise']
#: name=r_openshift_node_service_type, required=true, description="System service type"
#: name=r_openshift_node_image_tag, required=true, description="Node image tag to pull for containerized deployment"

# List of optional undefined variables
#: name=r_openshift_node_system_images_registry, description="System image registry to pull images from", required_when=["r_openshift_node_is_containerized | bool", "r_openshift_node_is_node_system_container | bool"], required_when=["r_openshift_node_is_containerized | bool", "r_openshift_node_is_openvswitch_system_container | bool", "r_openshift_node_use_openshift_sdn | bool"]

#: description="Set to deploy containerized node"
r_openshift_node_is_containerized: false
#: description="Set to deploy a node over AH"
r_openshift_node_is_atomic: false
```

The role variables can be broken down intro three categories:
* required role variables but undefined: role variables that must be always defined but without a default value
* optional role variables but undefined: role variables that are undefined by default but can be defined
* role variables that are always defined with a default value: role variables that can be overwritten

All three categories can be annotated with the following keywords:
* name: optional annotation used for role variables that are undefined, used when a table of role variables and pre-checks are generated
* description: short and accurate description of a role variable
* required: set to `false` if not specified, if set to `true` the role variable is required (forced by generated pre-checks tasks)
* choices: a list of acceptable values of a role variables
* required_when: a list of conjuncts under which a role variable must be defined

A table of role variables and a sequence of pre-checks are generated from the specified annotations.

All variables under `var/main.yml` are considered local variables.

#### We should check all relevant role variables are properly set

A list of tasks checking role variables can be generated based on the role variable annotations.
Given a list of role variables and their properties (e.g. if a variable is required, a list of accepted values)
can change over time, it is important to keep the checks in sync with the `default/main.yml`.
The following checks can be generated:

```yaml
- name: "Fail if r_openshift_node_deployment_type is not defined"
  fail:
    msg: "r_openshift_node_deployment_type must be specified for this role"
  when:
  - r_openshift_node_deployment_type is not defined

- name: Fail if invalid r_openshift_node_deployment_type provided
  fail:
    msg: "r_openshift_node_deployment_type can only be set to a single value from ['origin', 'openshift-enterprise']"
  when:
  - r_openshift_node_deployment_type is defined
  - r_openshift_node_deployment_type not in ['origin', 'openshift-enterprise']
```

All the checks can be stored into `tasks/pre_checks.yml` file and included in the main task file.

#### Propagation of values to role dependencies

A role can depend on another role that has its own set of role variables. There are two ways how to propagate values to role dependencies. First approach requires a caller has a knowledge of all role dependency variables:

```yaml
roles:
- role: etcd
  r_etcd_client_port: 2379
  r_etcd_peer_port: 2380
  r_etcd_common_etcd_runtime: docker
  r_etcd_common_embedded_etcd: false
```

Here the `etcd` role depends on `etcd_common` role.
The second approach is to duplicate all role dependency variables:

```yaml
roles:
- role: etcd
  r_etcd_client_port: 2379
  r_etcd_peer_port: 2380
  r_etcd_etcd_runtime: docker
  r_etcd_embedded_etcd: false
```

and write all the duplicated role variables into their corresponding
dependency variables in `etcd/meta/main.yml`:

```yaml
dependencies:
- role: etcd_common
  r_etcd_common_etcd_runtime: "{{ r_etcd_etcd_runtime }}"
  r_etcd_common_embedded_etcd: "{{ r_etcd_embedded_etcd }}"
```

One can use `include_role` instead of `roles`:

```yaml
include_role:
  name: etcd
vars:
  r_etcd_client_port: 2379
  r_etcd_peer_port: 2380
  r_etcd_etcd_runtime: docker
  r_etcd_embedded_etcd: false
```

From the point of view of the caller the number of role variables
to be set does not change in both approaches.

**Advantages** of the second approach:
* role dependencies and role variables of dependencies can change transparently
* caller does not need any knowledge of role variables of dependencies

**Disadvantages**:
* role variables of dependencies has to be duplicated
* one must not forget to wire all duplicated variables inside `meta/main.yml` file (this step can be automatically generated)
* optional undefined variables can not be set this way (TODO(jchaloup): or can they? is that even needed, maybe all roles with optional undefined role variables should not be dependencies of another role)

### Local variables

All variables set inside a role has to be prefixed with `l_` string.
The only exception are role variables that are read outside of a role after
the role finishes.

### Role invocation

Based on a role caller some role variables are always defined,
some are defined only when corresponding inventory (or other global) variables are set.
E.g. although `r_openshift_node_is_containerized` is set to `false` be default,
the `openshift.common.is_containerized` is always set so it is safe to set the value unconditionally:
```yaml
- role: openshift_node
  r_openshift_node_is_containerized: "{{ openshift.common.is_containerized }}"
```

Some role variables like `r_openshift_node_kubelet_args` are optionally defined
and can not be set unless their corresponding inventory (or other playbook) variables
are set. So the proper way to set them is:
```yaml
- set_task:
    r_openshift_node_kubelet_args: "{{ openshift_node_kubelet_args }}"
  when: openshift_node_kubelet_args is defined

- include_role:
    name: openshift_node
  vars:
    r_openshift_node_is_containerized: "{{ openshift.common.is_containerized }}"
```

Thus, in general a role invocation corresponds to the following pattern:
```yaml
- set_task:
    r_ROLENAME_VARIABLE_i: "{{ GLOBAL_VARIABLE_i }}"
  when: GLOBAL_VARIABLE_i is defined
  # for i \in {1, ..., j}

- include_role:
    name: ROLE
  vars:
    r_ROLENAME_VARIABLE_i: "{{ GLOBAL_VARIABLE_i }}"
    # for i \in {j+1, ..., n}
```

The `j` denotes a number of role variables that are set only when corresponding
inventory (or other global) variables is defined.
The `n` denotes the total number of all role variables that are being set.
One way to convert all optionally set role variables is to set default values for all
inventory (and other global) variables.

Meantime, until the problem of optionally defined role variables is solved,
one can generate the list of the `set_task: ... when: ...` tasks automatically.

### Example

**Before applying the proposal**:

`openshift_node/tasks/main.yml`:
```yaml
- name: pull node image
  command: >
    docker pull {{ openshift_node_image_name }}:{{ openshift_node_image_tag }}
  register: docker_pull_result
```

**After:**

`openshift_node/defaults/main.yml`:
```yaml
# description="OpenShift node image name"
r_openshift_node_image_name: openshift-node
# description="OpenShift node image tag"
r_openshift_node_image_tag: v3.6.2
```

`openshift_node/tasks/main.yml`
```yaml
- name: pull node image
  command: >
    docker pull {{ r_openshift_node_image_name }}:{{ r_openshift_node_image_tag }}
  register: l_docker_pull_result
```

### Roadmap

1. refactor all roles to comply with the proposal
2. deal with the optionally defined role variables
3. have role tables in README.md files of all roles to be automatically generated
