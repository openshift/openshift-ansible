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

## References
* https://github.com/openshift/openshift-ansible/blob/master/roles/template_service_broker/
