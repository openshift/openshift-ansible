# OpenShift Metering

This playbook runs the [Openshift Metering role](../../roles/openshift_metering).
See the role for more information.

## Prequisites:

This playbook requires Openshift Monitoring to be installed, to install it set this variable:

```yaml
openshift_monitoring_deploy: true
```

## Installation

To install Openshift Metering, set this variable:

```yaml
openshift_metering_install: true
```

To uninstall, set:

```yaml
openshift_metering_install: false
```

Then run:

```bash
ansible-playbook playbooks/openshift-metering/config.yml
```

## GCP Development

The `gcp-config.yml` playbook is useful for ad-hoc installation in an existing GCE cluster:

```bash
ansible-playbook playbooks/openshift-metering/gcp-config.yml
```
