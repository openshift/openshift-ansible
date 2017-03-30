# Scaffolding for decomposing large roles

## Why?

Currently we have roles that are very large and encompass a lot of different
components. This makes for a lot of logic required within the role, can
create complex conditionals, and increases the learning curve for the role.

## How?

Creating a guide on how to approach breaking up a large role into smaller,
component based, roles. Also describe how to develop new roles, to avoid creating
large roles.

## Proposal

Create a new guide or append to the current contributing guide a process for
identifying large roles that can be split up, and how to compose smaller roles
going forward.

### Large roles

A role should be considered for decomposition if it:

1) Configures/installs more than one product.
1) Can configure multiple variations of the same product that can live
side by side.
1) Has different entry points for upgrading and installing a product

Large roles should be responsible for:

1) Composing smaller roles to provide a full solution such as an Openshift Master
1) Ensuring that smaller roles are called in the correct order if necessary
1) Calling smaller roles with their required variables
1) Performing prerequisite tasks that small roles may depend on being in place
(openshift_logging certificate generation for example)

### Small roles

A small role should be able to:

1) Be deployed independently of other products (this is different than requiring
being installed after other base components such as OCP)
1) Be self contained and able to determine facts that it requires to complete
1) Fail fast when facts it requires are not available or are invalid
1) "Make it so" based on provided variables and anything that may be required
as part of doing such (this should include data migrations)

### Example using decomposition of openshift_logging

The `openshift_logging` role was created as a port from the deployer image for
the `3.5` deliverable. It was a large role that created the service accounts,
configmaps, secrets, routes, and deployment configs/daemonset required for each
of its different components (Fluentd, Kibana, Curator, Elasticsearch).

It was possible to configure any of the components independently of one another,
up to a point. However, it was an all of nothing installation and there was a
need from customers to be able to do things like just deploy Fluentd.

Also being able to support multiple versions of configuration files would become
increasingly messy with a large role. Especially if the components had changes
at different intervals.

#### Folding of responsibility

There was a duplicate of work within the installation of three of the four logging
components where there was a possibility to deploy both an 'operations' and
'non-operations' cluster side-by-side. The first step was to collapse that
duplicate work into a single path and allow a variable to be provided to
configure such that either possibility could be created.

#### Consolidation of responsibility

The generation of OCP objects required for each component were being created in
the same task file, all Service Accounts were created at the same time, all secrets,
configmaps, etc. The only components that were not generated at the same time were
the deployment configs and the daemonset. The second step was to make the small
roles self contained and generate their own required objects.

#### Consideration for prerequisites

Currently the Aggregated Logging stack generates its own certificates as it has
some requirements that prevent it from utilizing the OCP cert generation service.
In order to make sure that all components were able to trust one another as they
did previously, until the cert generation service can be used, the certificate
generation is being handled within the top level `openshift_logging` role and
providing the location of the generated certificates to the individual roles.

#### Snippets

openshift_logging/tasks/install_logging.yaml
```
- name: Install logging
  include: "{{ role_path }}/tasks/install_support.yaml"
  when: openshift_hosted_logging_install | default(true) | bool


## Elasticsearch
- include_role:
    name: openshift_logging_elasticsearch
  vars:
    generated_certs_dir: "{{openshift.common.config_base}}/logging"

- include_role:
    name: openshift_logging_elasticsearch
  vars:
    generated_certs_dir: "{{openshift.common.config_base}}/logging"
    openshift_logging_es_ops_deployment: true
  when:
  - openshift_logging_use_ops | bool


## Kibana
- include_role:
    name: openshift_logging_kibana
  vars:
    generated_certs_dir: "{{openshift.common.config_base}}/logging"

- include_role:
    name: openshift_logging_kibana
  vars:
    generated_certs_dir: "{{openshift.common.config_base}}/logging"
    openshift_logging_kibana_ops_deployment: true
  when:
  - openshift_logging_use_ops | bool


## Curator
- include_role:
    name: openshift_logging_curator
  vars:
    generated_certs_dir: "{{openshift.common.config_base}}/logging"

- include_role:
    name: openshift_logging_curator
  vars:
    generated_certs_dir: "{{openshift.common.config_base}}/logging"
    openshift_logging_curator_ops_deployment: true
  when:
  - openshift_logging_use_ops | bool


## Fluentd
- include_role:
    name: openshift_logging_fluentd
  vars:
    generated_certs_dir: "{{openshift.common.config_base}}/logging"

- include: update_master_config.yaml
```

openshift_logging/tasks/install_support.yaml [old]
```
---
# This is the base configuration for installing the other components
- name: Check for logging project already exists
  command: >
    {{ openshift.common.client_binary }} --config={{ mktemp.stdout }}/admin.kubeconfig get project {{openshift_logging_namespace}} --no-headers
  register: logging_project_result
  ignore_errors: yes
  when: not ansible_check_mode
  changed_when: no

- name: "Create logging project"
  command: >
    {{ openshift.common.admin_binary }} --config={{ mktemp.stdout }}/admin.kubeconfig new-project {{openshift_logging_namespace}}
  when: not ansible_check_mode and "not found" in logging_project_result.stderr

- name: Create logging cert directory
  file: path={{openshift.common.config_base}}/logging state=directory mode=0755
  changed_when: False
  check_mode: no

- include: generate_certs.yaml
  vars:
    generated_certs_dir: "{{openshift.common.config_base}}/logging"

- name: Create temp directory for all our templates
  file: path={{mktemp.stdout}}/templates state=directory mode=0755
  changed_when: False
  check_mode: no

- include: generate_secrets.yaml
  vars:
    generated_certs_dir: "{{openshift.common.config_base}}/logging"

- include: generate_configmaps.yaml

- include: generate_services.yaml

- name: Generate kibana-proxy oauth client
  template: src=oauth-client.j2 dest={{mktemp.stdout}}/templates/oauth-client.yaml
  vars:
    secret: "{{oauth_secret}}"
  when: oauth_secret is defined
  check_mode: no
  changed_when: no

- include: generate_clusterroles.yaml

- include: generate_rolebindings.yaml

- include: generate_clusterrolebindings.yaml

- include: generate_serviceaccounts.yaml

- include: generate_routes.yaml
```

openshift_logging/tasks/install_support.yaml [new]
```
---
# This is the base configuration for installing the other components
- name: Set logging project
  oc_project:
    state: present
    name: "{{ openshift_logging_namespace }}"

- name: Create logging cert directory
  file: path={{openshift.common.config_base}}/logging state=directory mode=0755
  changed_when: False
  check_mode: no

- include: generate_certs.yaml
  vars:
    generated_certs_dir: "{{openshift.common.config_base}}/logging"

- name: Create temp directory for all our templates
  file: path={{mktemp.stdout}}/templates state=directory mode=0755
  changed_when: False
  check_mode: no
```

# Limitations

There will always be exceptions for some of these rules, however the majority of
roles should be able to fall within these guidelines.

# Additional considerations

Playbooks including playbooks (link to rteague's presentation?)
