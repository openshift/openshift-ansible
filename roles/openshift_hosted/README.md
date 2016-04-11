OpenShift Hosted
================

OpenShift Hosted Resources

* OpenShift Router

Requirements
------------

This role requires a running OpenShift cluster with nodes labeled to
match the openshift_hosted_router_selector (default: region=infra).

Role Variables
--------------

From this role:

| Name                                | Default value                            | Description                                                                                                          |
|-------------------------------------|------------------------------------------|----------------------------------------------------------------------------------------------------------------------|
| openshift_hosted_router_certificate | None                                     | Dictionary containing "certfile" and "keyfile" keys with values containing paths to local certificate files.         |
| openshift_hosted_router_registryurl | 'openshift3/ose-${component}:${version}' | The image to base the OpenShift router on.                                                                           |
| openshift_hosted_router_replicas    | Number of nodes matching selector        | The number of replicas to configure.                                                                                 |
| openshift_hosted_router_selector    | region=infra                             | Node selector used when creating router. The OpenShift router will only be deployed to nodes matching this selector. |

Dependencies
------------

* openshift_common
* openshift_hosted_facts

Example Playbook
----------------

```
- name: Create hosted resources
  hosts: oo_first_master
  roles:
  - role: openshift_hosted
    openshift_hosted_router_certificate:
      certfile: /path/to/my-router.crt
      keyfile: /path/to/my-router.key
    openshift_hosted_router_registryurl: 'registry.access.redhat.com/openshift3/ose-haproxy-router:v3.0.2.0'
    openshift_hosted_router_selector: 'type=infra'
```

License
-------

Apache License, Version 2.0

Author Information
------------------

Red Hat openshift@redhat.com
