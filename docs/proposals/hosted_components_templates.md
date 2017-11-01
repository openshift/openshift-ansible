# Use OCP templates to install hosted components

## Description
Currently most of our hosted components have their own repositories where they
maintain changes and then need to synchronize those changes within their
respective roles. This can cause cause delays and times where features don't
match up with what is installed or can be configured.

## Rationale
As was piloted with the Template Service Broker, a role was created to process
and configure OCP templates that were synchronized (currently still a manual
process) from the origin repo where the component resides.

This allowed any changes for the installation to be maintained by the developers
and keep them from needing to be fluent with Ansible. It also afforded a level
of abstraction from needing to keep in sync with TSB related changes and then
translate them to changes within an Ansible role.

## Design
We should describe a way to structure roles to reuse the templates that may be
being produced already for components to install. This also can increase
developer buy in for cases where they are hesitant to create an Ansible role
for installing their product. It also aligns with how `oc cluster up` installs
components, using OCP templates.

## User Story
As a developer on OpenShift-Ansible,
I want to roles for hosted components to process OCP templates that are provided
  by the developer of the component
so that the majority of on-boarding and supporting a hosted component be the
  responsibility of the developer of the component, reducing the amount of
  copypasta and translating to Ansible that is done as updates are made.

## Acceptance Criteria
* Verify that roles are simple and used to install|update|remove the component
* Verify that roles leverage oc and provided templates to maintain the objects
  for the component
* Verify that the templates are synchronized from the component's repository to
  openshift-ansible under the repo level files dir
* Verify that roles are idempotent (side effects only when necessary)

## References
* https://github.com/openshift/openshift-ansible/blob/master/roles/template_service_broker/

### template_service_broker role snippets

[template_service_broker/tasks/install.yml](https://github.com/openshift/openshift-ansible/blob/master/roles/template_service_broker/tasks/install.yml#L24-L85)
```yaml
## This is copying the files we use from openshift-ansible/files/origin-components/ to the host
- copy:
    src: "{{ __tsb_files_location }}/{{ item }}"
    dest: "{{ mktemp.stdout }}/{{ item }}"
  with_items:
    - "{{ __tsb_template_file }}"
    - "{{ __tsb_rbac_file }}"
    - "{{ __tsb_broker_file }}"
    - "{{ __tsb_config_file }}"

## This shouldn't be common for most our other roles, here we are modifying an upstream
##  config file that we have copied to the host to add additional namespaces since the
##  default doesn't suffice.
- yedit:
    src: "{{ mktemp.stdout }}/{{ __tsb_config_file }}"
    key: templateNamespaces
    value: "{{ openshift_template_service_broker_namespaces }}"
    value_type: list

## Since the contents of the config file we've updated needs to be provided as a
##  param value, we use slurp to get them
- slurp:
    src: "{{ mktemp.stdout }}/{{ __tsb_config_file }}"
  register: config

## Here we are using oc process and piping to kubectl apply, providing values for
##  params that we should configure based on values provided in the inventory.
##  We use --param so we can consume the template from origin without modifying it,
##  removing the risk of adding stale configurations through editing.
- name: Apply template file
  shell: >
    oc process -f "{{ mktemp.stdout }}/{{ __tsb_template_file }}"
    --param API_SERVER_CONFIG="{{ config['content'] | b64decode }}"
    --param IMAGE="{{ template_service_broker_prefix }}{{ template_service_broker_image_name }}:{{ template_service_broker_version }}"
    | kubectl apply -f -

## Similar to the above, we are using oc process to create a list of api objects
##  which we then pipe to different oc commands. In this case we need to reconcile
##  auth settings so we're piping to oc auth reconcile
# reconcile with rbac
- name: Reconcile with RBAC file
  shell: >
    oc process -f "{{ mktemp.stdout }}/{{ __tsb_rbac_file }}" | oc auth reconcile -f -

## As part of setting up the TSB we need to also update the extension file used
##  by the console
- name: copy tech preview extension file for service console UI
  copy:
    src: openshift-ansible-catalog-console.js
    dest: /etc/origin/master/openshift-ansible-catalog-console.js

# Check that the TSB is running
- name: Verify that TSB is running
  command: >
    curl -k https://apiserver.openshift-template-service-broker.svc/healthz
  args:
    # Disables the following warning:
    # Consider using get_url or uri module rather than running curl
    warn: no
  register: api_health
  until: api_health.stdout == 'ok'
  retries: 120
  delay: 1
  changed_when: false

- set_fact:
    openshift_master_config_dir: "{{ openshift.common.config_base }}/master"
  when: openshift_master_config_dir is undefined

- slurp:
    src: "{{ openshift_master_config_dir }}/service-signer.crt"
  register: __ca_bundle

## The final part of the TSB is to make sure we have a broker object created with
##  the correct CA bundle, so we make sure to pass that as a param and then
##  pipe the resulting object list to oc apply to be created idempotently
# Register with broker
- name: Register TSB with broker
  shell: >
    oc process -f "{{ mktemp.stdout }}/{{ __tsb_broker_file }}" --param CA_BUNDLE="{{ __ca_bundle.content }}" | oc apply -f -
```

[template_service_broker/vars/main.yml](https://github.com/openshift/openshift-ansible/blob/master/roles/template_service_broker/vars/main.yml)
```yaml
---
__tsb_files_location: "../../../files/origin-components/"

__tsb_template_file: "apiserver-template.yaml"
__tsb_config_file: "apiserver-config.yaml"
__tsb_rbac_file: "rbac-template.yaml"
__tsb_broker_file: "template-service-broker-registration.yaml"
```
