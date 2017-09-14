# Template Flexibility

## Description
Templates are somewhat inflexible, rely heavily on openshift-ansible developers
to not break existing functionality, and rely heavily on openshift-ansible
developers to keep templates up to date to provide the newest features.

We do not currently have a good 'user story' around managing configuration files
of a running cluster.  This has led to the situation of users modifying various
templates and configuration files outside of openshift-ansible, which causes
downtime during upgrades or re-runs of certain plays.

## Rationale
This proposal consists of 3 areas of interest.  Each area of interest improves
flexibility over the existing implementation.  Each area of interest is
complimentary.  Each area of interest is 100% non-breaking for the existing
method of consuming templates.

These changes can be considered, in whole or in part, a 'drop in replacement'
for how we currently handle templates.

### Custom templates
The ansible template module allows specifying src location via variable.

Proposal: modify src to a variable with default to the existing template file.

This allows users to specify some other template that may be available on
their deployment host via an absolute path.  This will allow users to carry
custom templates out-of-tree without having to maintain forks of the project.

Caveats: Users should be informed that if they choose to utilize these variables
that they will be in an 'unknown' configuration as far as openshift-ansible
is concerned.  It will be difficult for us to help users coordinate upgrades
if we are not managing their configuration files, and users will be responsible
for resolving any differences needed between versions.

### Template booleans
In the extreme case, some users don't want us to touch templates whatsoever.

Proposal: add a boolean to each template task to allow users to skip placement
of the template. These booleans should be properly namespaced, and there
should not be any variable that controls multiple templates at once.

This will allow advanced users to control configuration files outside of
openshift-ansible without having to worry about openshift-ansible interfering
with their operations.

Caveats: Users should be informed that if they choose to utilize these booleans
that they will be in an 'unknown' configuration as far as openshift-ansible
is concerned.  It will be difficult for us to help users coordinate upgrades
if we are not managing their configuration files, and users will be responsible
for resolving any differences needed between versions.

### Switch to config_template
In place of using the 'template' module directly, a custom action plugin
was created by the openstack-ansible project, and adopted by the ceph-ansible
project.

config_template is an extension to the copy module, but utilizes jinja2 template
files in the same manner as the template module.  config_template is an action
module, so all changes are made on the deployment host before being copied to
the target host.

config_template allows users to supply a dictionary of key-value pairs to:
1) Add items that are not present in the template
2) Override items that are present in the template

config_template gives users the flexibility of using our templates in whole or
in part.

config_template has current support for ini, json, and yaml files.

config_template cannot, at this time, make modifications to nested values
directly.  For example, in a yaml file, a.b.c, c cannot be modified, a must
be supplied in it's entirety. It should be easy to merge the functionality of
yedit with config_template or otherwise modify config_template to provide this
functionality in the near future.

## Design

### Custom templates
```yaml
- template:
    dest: "{{ openshift_master_config_file }}"
    src: "{{ openshift_master_config_template_path | default('master.yaml.v1.j2') }}"
```

### Template booleans

With 'custom templates' suggestion above
```yaml
- template:
    dest: "{{ openshift_master_config_file }}"
    src: "{{ openshift_master_config_template_path | default('master.yaml.v1.j2') }}"
  when: "{{ openshift_master_config_template_path_manage | default(True) }}"
```
Without 'custom templates' section above
```yaml
- template:
    dest: "{{ openshift_master_config_file }}"
    src: master.yaml.v1.j2
  when: "{{ openshift_master_config_template_path_manage | default(True) }}"
```

### config_template
With both suggestions above
```yaml
# tasks/main.yml
- config_template:
    dest: "{{ openshift_master_config_file }}"
    src: "{{ openshift_master_config_template_path | default('master.yaml.v1.j2') }}"
    config_overrides: "{{ openshift_master_config_overrides | default({}) }}"
    config_type: "yaml"
  when: "{{ openshift_master_config_template_path_manage | default(True) }}"
```

```yaml
# templates/master.yaml.v1.j2

x1: {{ x1_var }}
x2: "x2 is a string"
x3: "this will be overridden"

```

```yaml
# defaults/main.yml
x1_var: 33

openshift_master_config_overrides:
  x3: "this is a new overriding value"
  d1:
    - "item1"
    - item2:
      a: 1
      b: 2
  d2: "d2 is a string"
  d3:
    a: 3
    b: 4
```

```yaml
# output of config_template with overrides
d1:
  - item1
  - a: 1
    b: 2
    item2: null
d2: d2 is a string
d3:
  a: 3
  b: 4
x1: 33
x2: x2 is a string
x3: this is a new overriding value
```

## Checklist
I'm not sure what to do with this section.

## User Story
As a user on OpenShift-Ansible,
I want to have more flexibility in configuration templates.

so that...

I can
1) Provide my own templates,
2) Prevent openshift-ansible from managing my configs because I use another
process to configure and maintain my configuration files,
3) and/or Override and/or add sections to templates that openshift-ansible
provides, and I just want to tweak/add a few things without filing a PR.

## Acceptance Criteria
* One or more areas of interest are implemented
* New behavior is documented.

## References
* config_template source: https://github.com/openstack/openstack-ansible-plugins/blob/master/action/config_template.py
* config_template example project: https://github.com/michaelgugino/config-template-example
* ceph-ansible uses config-template: https://github.com/ceph/ceph-ansible/blob/master/plugins/actions/config_template.py
