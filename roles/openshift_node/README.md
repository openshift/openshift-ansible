OpenShift Node
================================

Node service installation

Requirements
------------

* Ansible 2.2
* One or more Master servers
* A RHEL 7.1 host pre-configured with access to the rhel-7-server-rpms,
rhel-7-server-extras-rpms, and rhel-7-server-ose-3.0-rpms repos

Role Variables
--------------
From this role:

| Name                       | Default value         |                                                          |
|----------------------------|-----------------------|----------------------------------------------------------|
| oreg_url                   | UNDEF (Optional)      | Default docker registry to use                           |
| oreg_url_node              | UNDEF (Optional)      | Default docker registry to use, specifically on the node |

Dependencies
------------


Example Playbook
----------------

Notes
-----

Currently we support re-labeling nodes but we don't re-schedule running pods nor remove existing labels. That means you will have to trigger the re-schedulling manually. To re-schedule your pods, just follow the steps below:

```
oc adm manage-node --schedulable=false ${NODE}
oc adm manage-node --drain ${NODE}
oc adm manage-node --schedulable=true ${NODE}
````

> If you are using version less than 1.5/3.5 you must replace `--drain` with `--evacuate`.


TODO

License
-------

Apache License, Version 2.0

Author Information
------------------

TODO
