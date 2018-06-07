# OpenShift Metering

This role installs the OpenShift [Metering](https://github.com/operator-framework/operator-metering), which supports metering operators and applications in Kubernetes and producing reports on this metered information.

### **NOTE: This component is unsupported in OCP at this time.**

## Installation

To install Openshift Metering, set this variable:

```yaml
openshift_metering_install: true
```

To uninstall, set:

```yaml
openshift_metering_install: false
```

## Configuration

The metering operator comes with a default no-op [Metering configuration][metering-config].
To supply additional configuration options set the `openshift_metering_config` variable to a dictionary containing the contents of the `Metering` `spec` field you wish to set.

For example:

```
openshift_metering_config:
  metering-operator:
    config:
      awsAccessKeyID: "REPLACEME"
```

Updating the operator itself to a custom image can be done by setting `openshift_metering_operator_image` to a docker image and tag that should be used.

For example:

```
openshift_metering_config: quay.io/coreos/chargeback-helm-operator:latest
```

Using a custom project/namespace can be done by specifying `__openshift_metering_namespace`.

## License

Apache License, Version 2.0

[metering-config]: https://github.com/operator-framework/operator-metering/blob/master/Documentation/metering-config.md
