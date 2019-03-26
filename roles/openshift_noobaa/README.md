## Role: openshift_noobaa

The whole work is done by the `openshift_noobaa` role. This
role can handle the deployment/removal/upgrade of NooBaa (if it is to be hosted on the
OpenShift cluster master).

## Requirements

* Ansible 2.4

## Role Variables

```
# NooBaa namespace/project that will be created and used for deployment/upgrade/removal
noobaa_namespace: STRING (example: noobaa)

# Minimum CPU to be allocated for the container
min_cpu: STRING (example: "500m")

# Minimum MEMORY to be allocated for the container
min_memory: STRING (example: "1Gi")

# Maximum CPU to be allocated for the container
max_cpu: STRING (example: "4")

# Maximum MEMORY to be allocated for the container
max_memory: STRING (example: "8Gi")
```

## Dependencies

- role: lib_openshift
- role: openshift_facts

## License

Apache 2.0

## Author Information

Evgeniy Belyi (jeniawhite92@gmail.com)