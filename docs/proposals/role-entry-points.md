# Entry-point based roles

## Variables inside a role are too open

Each role consists of a set of tasks and variables read/set in some of the tasks.
Some of the tasks can store their results into registered variables,
e.g. store stdout of a docker pull command.
Some of the tasks may be run only under certain conditions that are generated
outside of a role, e.g. pull images only if a deployment is containerized.
Some of the tasks are run only if a certain variable is defined,
e.g. add additional Kubelet arguments into the `node-config.yml`
if `kubelet_additional_args` inventory variable is defined.

Some roles work with a lot of variables that from a point of view of a role are uninvited citizens.
Some of the variables are set inside a role, some of them are set outside of a role.
The variables outside of a role are hard to track, hard to determine their value or
a condition under which they are defined. These unknown facts make a role harder
to maintain, harder to be closed with respect to variables and to become practically modular.

## Proposal

Make a role that conforms to the following conditions:
* none of the variables read/set inside a role are global
* all variables inside a role are `r_` (`r` standing for a role) and/or `__` (for private) prefixed
* all values are propagated to a role through `r_` prefixed variables only
* all values that are set inside a role are read outside of a role through `r_` prefixed variables only
* all available `r_` prefixed variables are documented and checked before a main role task is run
* a table of `r_` prefixed variables in README.md is automatically generated

### Terminology

**Role variables**: All `r_` prefixed variables read/set inside a role

**Local/Private variables**: All `__` prefixed variables set inside a role

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
* can be shared across different Ansible solutions (increases modularity)
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
r_openshift_node_is_containerized: "{{ __openshift_node_is_containerized }}"
__openshift_node_is_containerized: false

#: description="Set to deploy a node over AH"
r_openshift_node_is_atomic: "{{ __openshift_node_is_atomic }}"
__openshift_node_is_atomic: false
```

Notice the role variable pairs, e.g. (`r_openshift_node_is_containerized`, `__openshift_node_is_containerized`).
The former is a role variable available in role API, the latter is a default for the former role variable.
If the former role variable is omitted (defined later), the default one overwrites the former one.

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

#### Omitted role variables

Once an Ansible variable is defined, it can not be undefined.
That can be an issue if a play calls a role that has role variables
set to inventory variables that are optional, i.e. does not have to be defined.

Assume a role that is invoked in the following way:
```yaml
- include_role:
    name: <role>
  vars:
    r_<role>_variable: "{{ inventory_variable }}"
```

If the `inventory_variable` is defined, the role is invoked successfully.
If the variable is not defined, we either:

* have to check and set the `r_<role>_variable` conditionally, or
* we need to use the `default` filter.

The former case can lead to a sequence of `set_fact: ... when: ... is defined` tasks.
Additionally, the role variables are set separately from the role invocation.

The latter case can lead to a sequence of `r_<role>_<variable>: "{{ <inventory_variable> | default(<default>) }}"` lines.
To apply the `default(<default>)` filter one needs to know a default value of
corresponding role variable (which leads to value duplication that is already set in the role).
Thus, to eliminate default value duplication and to keep role variables
definition in the role invocation expression, one can use the `default(omit)`
filter form:

```yaml
- include_role:
    name: <role>
  vars:
    r_<role>_<variable>: "{{ inventory_<variable> | default(omit) }}"
    r_<role>_<variable>: "{{ inventory_<variable> | default(omit) }}"
    ...
```

Currently, the `omit` keyword is correctly interpreted by Ansible only
when used with module arguments (https://github.com/ansible/ansible/issues/13619).
For that reason the role has to advocate the following pattern to properly
interpret "omitted" role variables:

```yaml
- name: "Set r_openshift_node_is_containerized to default if omited"
  set_fact:
    r_openshift_node_is_containerized: "{{ __openshift_node_is_containerized }}"
  when:
  - __omit_str in r_openshift_node_is_containerized | string
```

**Explanation**: The `r_openshift_node_is_containerized` is set to `__openshift_node_is_containerized`
only when the role variable is set to `omit`. Internally the `omit` corresponds to a string
accepted by `__omit_place_holder__[\da-e]{40}` regex. Thus, if the role variable
value contains the `__omit_place_holder__` string (stored inside the `__omit_str` variable),
the role variable is considered to be "undefined" and thus set to its default value.
This way, the role variables can be set to non-role variables that are optionally defined
in a compact way.

Since the `__omit_str` can be used on multiple places (e.g. tasks, templates),
it is defined in `defaults/main.yml` as `__omit_str: "__{{ omit.split('__')[1] }}__"`.

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

### Local variables

All variables set inside a role has to be prefixed with `__` string.
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
are set. So the proposed way to set them is:
```yaml
- role: openshift_node
  r_openshift_node_kubelet_args: "{{ openshift_node_kubelet_args | default(omit) }}"
```

Thus, in general the proposed way to invoke a role corresponds to the following pattern:
```yaml
- include_role:
    name: <role>
  vars:
    r_<role>_<variable>_1: "{{ <global_variable>_1 | default(omit) }}"
    ...
    r_<role>_<variable>_j: "{{ <global_variable>_j | default(omit) }}"
    r_<role>_<variable>_k: "{{ <global_variable>_k }}"
    ...
    r_<role>_<variable>_n: "{{ <global_variable>_n }}"
```

The `j` denotes a number of role variables that are set to non-role variables
that does not have to be defined.
The `n` denotes the total number of all role variables that are set.

### Example

**Before applying the proposal**:

`openshift_node/tasks/main.yml`:
```yaml
...
- name: pull node image
  command: >
    docker pull {{ openshift_node_image_name }}:{{ openshift_node_image_tag }}
  register: docker_pull_result
...
```

`playbooks/common/openshift-node/config.yml`
```yaml
...
- role: openshift_node
...
```

**After:**

`openshift_node/defaults/main.yml`:
```yaml
__omit_str: "__{{ omit.split('__')[1] }}__"

# description="OpenShift node image name"
r_openshift_node_image_name: "{{ __openshift_node_image_name }}"
__openshift_node_image_name: openshift-node
# description="OpenShift node image tag"
r_openshift_node_image_tag: "{{ __openshift_node_image_tag }}"
__openshift_node_image_tag: v3.6.2
...
```

`openshift_node/tasks/main.yml`
```yaml
...
- name: pull node image
  command: >
    docker pull {{ r_openshift_node_image_name }}:{{ r_openshift_node_image_tag }}
  register: l_docker_pull_result
...
```

`openshift_node/tasks/pre-checks.yml`
```yaml
...
- name: "Set r_openshift_node_image_name to default if omited"
  set_fact:
    r_openshift_node_image_name: "{{ __openshift_node_image_name }}"
  when:
  - __omit_str in r_openshift_node_image_name | string

- name: "Set r_openshift_node_image_tag to default if omited"
  set_fact:
    r_openshift_node_image_tag: "{{ __openshift_node_image_tag }}"
  when:
  - __omit_str in r_openshift_node_image_tag | string
...
```

`playbooks/common/openshift-node/config.yml`
```yaml
...
- role: openshift_node
  r_openshift_node_image_name: "{{ openshift_node_image_name | default(omit) }}"
  r_openshift_node_image_tag: "{{ openshift_image_tag | default(omit) }}"
...
```

### Roadmap

1. refactor all roles to comply with the proposal
2. filter out all optionally defined role variables with `default(omit)` filter
3. have role tables in README.md files of all roles to be automatically generated
