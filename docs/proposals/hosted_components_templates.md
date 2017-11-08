# Use OCP templates and emulate ABPs to install hosted components

## Description
Currently most of our hosted components have their own repositories where they
maintain changes and then need to synchronize those changes within their
respective roles. This can cause cause delays and times where features don't
match up with what is installed or can be configured.

There is also a concern that copying files from one location to another can
cause cases where files are out of sync or versions don't align with what is
installed and what is configured (is what we configured correct for the image
version we installed).

## Rationale
As was piloted with the Template Service Broker, a role was created to process
and configure OCP templates that were synchronized (currently still a manual
process) from the origin repo where the component resides.

This allowed any changes for the installation to be maintained by the developers
and keep them from needing to be fluent with Ansible. It also afforded a level
of abstraction from needing to keep in sync with TSB related changes and then
translate them to changes within an Ansible role.

However, there is still the gap of ensuring our role configures changes appropriate
for the version of the component we are installing. Prior to 3.4 with Aggregated
Logging this was resolved and contained due to using a deployer pod, since everything
was versioned and contained within an artifact the Integration Services team
provided. This is something that is addressed again now with the Service Broker,
APBs are configured in such a way that a containerized install/uninstall is done
for the component.

## Design
We should describe a way to create a containerized playbook and role to mirror
what is done with ABPs for hosted components so that the openshift-ansible roles
would reuse these containers to install/uninstall these components.

The containerized role would follow the pattern used by the TSB within its
openshift-ansible role `template_service_broker` to maintain a lower learning
curve for those not familiar with ansible as well as still provide a unified
interface for installing the component (aligning with `oc cluster up` as it can
leverage these OCP template files).

Within the openshift-ansible role, installing in a way similar to APBs would
create an interface that would not need to change once the role is created,
with the exception being if new information need be passed into the container.

If hosted components adhere to the structure required for the Service Broker
to provision/deprovision bind/unbind it allows us to also open up the possibility
to set up these components through the UI. This could further lighten the load
placed on openshift-ansible and provide an alternative means to install hosted
components after an OCP installation is completed.

## User Story
As a developer on OpenShift-Ansible,
I want to roles for hosted components to run the APB container that is provided
  by the developer of the component
so that the majority of on-boarding and supporting a hosted component be the
  responsibility of the developer of the component, reducing the amount of
  copypasta, translating to Ansible, and changes within the openshift-ansible
  role that is done as updates are made.

## Acceptance Criteria
* Verify that roles are simple and used to install|update|remove the component
* Verify that roles leverage APB containers to maintain the objects
  for the component
* Verify that openshift-ansible roles are idempotent (side effects only when necessary)
* Verify that the component APB containers adhere to necessary structure so that
  it can be reused by the Serice Broker if desired
* Verify that the APB role and playbook leverage oc and provided templates to
  maintain the objects for the component
* Verify that APB container roles are idempotent (side effects only when necessary)

## References
* https://github.com/openshift/openshift-ansible/blob/master/roles/template_service_broker/
* https://github.com/ansibleplaybookbundle/manageiq-apb

### proposed example role snippets

```yaml
## There may need to be some other ansible specific changes like creating and removing
##   a temp dir that would be mounted to the container in cases where we provide certs
##   we would then want the role to wait on the container to complete, provide its
##   run status and then clean up after.

- command: >
    docker run apb/openshift-logging provision -e '{"key": "val", "key2": "val2"}'

## We may also want to pull the logs from the container in the case where we did
##   not complete successfully, otherwise we would only see it was successful
```

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

### manageiq-apb snippets

[manageiq-apb/roles/provision-manageiq-apb/tasks/main.yml](https://github.com/ansibleplaybookbundle/manageiq-apb/blob/master/roles/provision-manageiq-apb/tasks/main.yml)
```yaml
#############################################################################
# Provision manageiq-apb
# Provions ManageIQ - an open source management platform for Hybrid IT
#############################################################################


- name: create app pvc
  k8s_v1_persistent_volume_claim:
    name: manageiq-app #TODO: manageiq-app-pvc
    namespace: '{{ namespace }}'
    state: present
    access_modes:
      - ReadWriteOnce
    resources_requests:
      storage: '{{ manage_iq_app_volume_size }}'

- name: create postgresql pvc
  k8s_v1_persistent_volume_claim:
    name: manageiq-postgresql #TODO: manageiq-postgresql-pvc
    namespace: '{{ namespace }}'
    state: present
    access_modes:
      - ReadWriteOnce
    resources_requests:
      storage: '{{ manage_iq_pg_volume_size }}'


- name: create app service
  k8s_v1_service:
    name: manageiq-app
    namespace: '{{ namespace }}'
    labels:
      app: manageiq-apb
      service: manageiq-app
    selector:
      app: manageiq-apb
      service: manageiq-app
    ports:
      - name: port-80
        port: 80
        target_port: 80
      - name: port-443
        port: 443
        targetPort: 443


- name: create memcached service
  k8s_v1_service:
    name: manageiq-memcached
    namespace: '{{ namespace }}'
    labels:
      app: manageiq-apb
      service: manageiq-memcached
    selector:
      app: manageiq-apb
      service: manageiq-memcached
    ports:
      - name: port-11211
        port: 11211
        target_port: 11211


- name: create postgresql service
  k8s_v1_service:
    name: manageiq-postgresql
    namespace: '{{ namespace }}'
    labels:
      app: manageiq-apb
      service: manageiq-postgresql
    selector:
      app: manageiq-apb
      service: manageiq-postgresql
    ports:
      - name: port-5432
        port: 5432
        targetPort: 5432


- name: create app route
  openshift_v1_route:
    name: manageiq-app
    namespace: '{{ namespace }}'
    spec_port_target_port: port-443
    spec_tls_termination: passthrough
    labels:
      app: manageiq-apb
      service: manageiq-app
    to_name: manageiq-app


- name: create app deployment config
  openshift_v1_deployment_config:
    name: manageiq-app
    namespace: '{{ namespace }}'
    labels:
      app: manageiq-apb
      service: manageiq-app
    replicas: 1
    selector:
      app: manageiq-apb
      service: manageiq-app
    spec_template_metadata_labels:
      app: manageiq-apb
      service: manageiq-app
    containers:
      - env:
          - name: MIQ_MEMCACHED_PORT_11211_TCP
            value: "{{ manageiq_memcached_port_11211_tcp | string }}"
          - name: DATABASE_SERVICE_NAME
            value: "{{ database_service_name | string }}"
          - name: MIQ_POSTGRESQL_PORT_5432_TCP_ADDR
            value: "{{ manageiq_postgresql_5432_tcp_addr }}"
          - name: MIQ_POSTGRESQL_PORT_5432_TCP
            value: "{{ manageiq_postgresql_port_5432_tcp | string}}"
          - name: DATABASE_REGION
            value: "{{ database_region | string }}"
          - name: MIQ_POSTGRESQL_SERVICE_HOST
            value: "{{ manageiq_postgresql_service_host }}"
          - name: MIQ_MEMCACHED_PORT_11211_TCP_ADDR
            value: "{{ manageiq_memcached_port_11211_tcp_addr }}"
          - name: POSTGRESQL_PASSWORD
            value: "{{ postgresql_password }}"
          - name: MEMCACHED_SERVICE_NAME
            value: "{{ memcached_service_name }}"
          - name: APPLICATION_INIT_DELAY
            value: "{{ application_init_delay | string}}"
          - name: MIQ_MEMCACHED_PORT
            value: "{{ manageiq_memcached_port | string}}"
          - name: MIQ_POSTGRESQL_PORT
            value: "{{ manageiq_postgresql_port | string }}"
          - name: MIQ_MEMCACHED_SERVICE_HOST
            value: "{{ manageiq_memcached_service_host }}"
          - name: POSTGRESQL_USER
            value: "{{ postgresql_user }}"
          - name: POSTGRESQL_DATABASE
            value: "{{ postgresql_database }}"
        image: docker.io/manageiq/manageiq-pods:app-latest-fine
        name: manageiq-app
        ports:
        - container_port: 80
          protocol: TCP
        - container_port: 443
          protocol: TCP
        security_context:
          privileged: true
        termination_message_path: /dev/termination-log
        volume_mounts:
        - mount_path: /persistent
          name: manageiq-app
        working_dir: /
    volumes:
    - name: manageiq-app
      persistent_volume_claim:
        claim_name: manageiq-app
    test: false
    triggers:
    - type: ConfigChange



- name: create manageiq-memcached deployment config
  openshift_v1_deployment_config:
    name: manageiq-memcached
    namespace: '{{ namespace }}'
    labels:
      app: manageiq-apb
      service: manageiq-memcached
    replicas: 1
    selector:
      app: manageiq-apb
      service: manageiq-memcached
    spec_template_metadata_labels:
      app: manageiq-apb
      service: manageiq-memcached
    containers:
      - env:
          - name: MEMCACHED_MAX_MEMORY
            value: '{{ memcached_max_memory | string}}'
          - name: MEMCACHED_MAX_CONNECTIONS
            value: '{{ memcached_max_connections | string}}'
          - name: MEMCACHED_SLAB_PAGE_SIZE
            value: '{{ memcached_slab_page_size | string}}'
        image: docker.io/manageiq/manageiq-pods:memcached-latest
        name: manageiq-memcached
        ports:
        - container_port: 11211
          protocol: TCP
        security_context:
          privileged: true
        termination_message_path: /dev/termination-log
        working_dir: /
    test: false
    triggers:
    - type: ConfigChange


- name: create manageiq-postgresql deployment config
  openshift_v1_deployment_config:
    name: manageiq-postgresql
    namespace: '{{ namespace }}'
    labels:
      app: manageiq-apb
      service: manageiq-postgresql
    replicas: 1
    selector:
      app: manageiq-apb
      service: manageiq-postgresql
    spec_template_metadata_labels:
      app: manageiq-apb
      service: manageiq-postgresql
    strategy_type: Rolling
    strategy_rolling_params:
      interval_seconds: 1
      max_surge: 25%
      max_unavailable: 25%
      timeout_seconds: 600
      update_period_seconds: 1
    containers:
      - env:
          - name: POSTGRESQL_PASSWORD
            value: '{{ postgresql_password }}'
          - name: POSTGRESQL_USER
            value: '{{ postgresql_user }}'
          - name: POSTGRESQL_DATABASE
            value: '{{ postgresql_database }}'
        image: docker.io/manageiq/manageiq-pods:app-latest-fine
        name: manageiq-app
        ports:
        - container_port: 5432
          protocol: TCP
        security_context:
          privileged: true
        termination_message_path: /dev/termination-log
        volume_mounts:
        - mount_path: /var/lib/pgsql/data
          name: manageiq-postgresql
        working_dir: /
    volumes:
    - name: manageiq-postgresql
      persistent_volume_claim:
        claim_name: manageiq-postgresql
    test: false
    triggers:
    - type: ConfigChange
```

[manageiq-apb/playbooks/provision/yml](https://github.com/ansibleplaybookbundle/manageiq-apb/blob/master/playbooks/provision.yml)
```yaml

- name: manageiq-apb playbook to provision the application
  hosts: localhost
  gather_facts: false
  connection: local
  roles:
  - role: ansible.kubernetes-modules
    install_python_requirements: no
  - role: provision-manageiq-apb
    playbook_debug: false
```

[manageiq-apb/Dockerfile](https://github.com/ansibleplaybookbundle/manageiq-apb/blob/master/Dockerfile)
```
FROM ansibleplaybookbundle/apb-base

LABEL "com.redhat.apb.spec"=\
 < snipped >














COPY playbooks /opt/apb/actions
COPY roles /opt/ansible/roles
USER apb
```

[manageiq-apb/apb.yml](https://github.com/ansibleplaybookbundle/manageiq-apb/blob/master/apb.yml)
```yaml
version: 1.0
name: manageiq-apb
description: ManageIQ
bindable: False
async: optional
metadata:
  displayName: "ManageIQ (APB)"
  imageUrl: "https://s3.amazonaws.com/fusor/2017demo/ManageIQ.png"
  documentationUrl: "https://manageiq.org/docs/"
  longDescription: "ManageIQ is an open source management platform for Hybrid IT. It can manage small and large environments, and supports multiple technologies such as virtual machines, public clouds and containers."
  dependencies: ['docker.io/manageiq/manageiq-pods:app-latest-fine', 'docker.io/manageiq/manageiq-pods:memcached-latest', 'docker.io/manageiq/manageiq-pods:app-latest-fine']
  providerDisplayName: "Red Hat, Inc."
plans:
  - name: default
    description: Typical installation of ManageIQ
    free: True
    metadata:
      displayName: Default
      longDescription: This plan deploys ManageIQ
      cost: $0.00
    parameters:
      - name: application_init_delay
        title: web app time delay
        description: Time to delay web app startup
        type: int
        default: 60
      - name: database_region
        title: database region
        description: MIQ Instance Region
        type: int
        default: 1
      - name: database_service_name
        title: database service name
        description: Service Name for the database
        type: string
        default: manageiq-postgresql
      - name: memcached_max_connections
        title: max connections
        description: Maximum number of connections memcached will accept
        type: int
        default: 1024
      - name: memcached_max_memory
        title: max memory
        description: Maximum memory memcached will use in MB
        type: int
        default: 64
      - name: memcached_slab_page_size
        title: slab page size
        description: Memcached Slab Size in bytes
        type: string
        default: 1M
      - name: memcached_service_name
        title: memcached service name
        description: Service name of the memcached instance to use
        type: string
        default: manageiq-memcached
      - name: namespace
        title: namespace
        description: Namespace/Project to deploy to
        type: string
        default: manageiq-apb
      - name: postgresql_database
        title: database name
        description: postgresql database name
        type: string
        default: vmdb_production
      - name: postgresql_password
        title: database password
        description: postgresql database password
        type: string
        default: admin
      - name: postgresql_user
        title: database username
        description: postgresql database username
        type: string
        default: admin
#
```
