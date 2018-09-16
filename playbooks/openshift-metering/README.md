# OpenShift Metering

This playbook runs the [Openshift Metering role](../../roles/openshift_metering).
See the role for more information.

## Prequisites:

This playbook requires Openshift Monitoring to be installed, to install it set this variable:

```yaml
openshift_monitoring_deploy: true
```

## Installation

To install Openshift Metering, run the install playbook:

```bash
ansible-playbook playbooks/openshift-metering/config.yml
```

To uninstall, run the uninstall playbook:

```bash
ansible-playbook playbooks/openshift-metering/uninstall.yml
```

